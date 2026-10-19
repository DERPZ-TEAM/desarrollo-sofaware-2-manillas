"""
Comando para cargar datos iniciales:

    python manage.py seed_goldbracelets

Crea (sin duplicar si ya existen):
  - Un administrador y un cliente de demostración
  - Las categorías base
  - Brazaletes de ejemplo SOLO si la tabla de productos está vacía

Contraseñas de los usuarios demo:
  - Local: SEED_ADMIN_PASSWORD / SEED_CLIENTE_PASSWORD o, si no existen, las de ejemplo.
  - Producción (DEBUG=False): SOLO las variables de entorno. Sin ellas no se crean
    los usuarios demo, y si alguno aún tiene la clave de ejemplo se bloquea.
"""
import os
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from account.models import Categoria, Perfil, Producto

User = get_user_model()
IMAGENES = Path(__file__).resolve().parents[2] / 'static' / 'images'

PRODUCTOS_DEMO = [
    # nombre, categoría, precio, stock, tipo_oro, quilates, peso, talla, elaboración, imagen
    ('Pulsera Tejida Imperial', 'Pulseras tejidas', '185000', 12, 'amarillo', 18, '4.20', '18', 'manual', 'mailla1.jpg'),
    ('Pulsera Hilo Dorado Esencia', 'Pulseras tejidas', '98000', 25, 'laminado', None, '2.10', '16', 'manual', 'manilla2.jpg'),
    ('Brazalete Rosa Aurora', 'Brazaletes', '320000', 6, 'rosa', 14, '6.80', '18', 'maquina', 'manilla3.jpg'),
    ('Cadena Cartier Clásica', 'Cadenas', '450000', 4, 'amarillo', 18, '9.50', '20', 'maquina', None),
    ('Pulsera Balines Golfi', 'Pulseras tejidas', '65000', 40, 'golfi', None, '1.80', '18', 'manual', None),
    ('Brazalete Oro Blanco Luna', 'Brazaletes', '520000', 2, 'blanco', 18, '7.30', '18', 'maquina', None),
]


class Command(BaseCommand):
    help = 'Crea administrador, cliente demo, categorías y brazaletes de ejemplo.'

    def _clave(self, variable, clave_demo):
        """Contraseña para un usuario demo.

        - Local (DEBUG=True): usa la variable de entorno o la clave de ejemplo.
        - Producción: SOLO la variable de entorno. Sin ella devuelve None y el
          usuario no se crea, porque la clave de ejemplo está publicada en la
          documentación y cualquiera podría usarla.
        """
        return os.environ.get(variable) or (clave_demo if settings.DEBUG else None)

    def _bloquear_si_clave_publica(self, username, clave_demo):
        """En producción, deja sin contraseña a una cuenta que aún use la clave de ejemplo."""
        user = User.objects.filter(username=username).first()
        if user and not settings.DEBUG and user.check_password(clave_demo):
            user.set_unusable_password()
            user.save(update_fields=['password'])
            self.stdout.write(self.style.WARNING(
                f'  La cuenta "{username}" tenía la contraseña de ejemplo: se dejó sin contraseña.'
            ))

    @transaction.atomic
    def handle(self, *args, **options):
        clave_admin = self._clave('SEED_ADMIN_PASSWORD', 'AdminGold123')
        clave_cliente = self._clave('SEED_CLIENTE_PASSWORD', 'Cliente123')

        if clave_admin:
            admin, creado = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@goldbracelets.com', 'first_name': 'Ana', 'last_name': 'Gestión'},
            )
            admin.is_staff = True
            admin.is_superuser = True
            if creado or os.environ.get('SEED_ADMIN_PASSWORD'):
                admin.set_password(clave_admin)
            admin.save()   # la señal pone rol=admin en el Perfil
        else:
            self._bloquear_si_clave_publica('admin', 'AdminGold123')

        if clave_cliente:
            cliente, creado = User.objects.get_or_create(
                username='cliente',
                defaults={'email': 'cliente@goldbracelets.com', 'first_name': 'Laura', 'last_name': 'Pérez'},
            )
            if creado:
                cliente.set_password(clave_cliente)
                cliente.save()
                Perfil.objects.filter(usuario=cliente).update(
                    telefono='3001234567', direccion='Calle 10 # 5-20', ciudad='Cali', departamento='Valle del Cauca',
                )
        else:
            self._bloquear_si_clave_publica('cliente', 'Cliente123')

        categorias = {}
        for i, nombre in enumerate(['Pulseras tejidas', 'Brazaletes', 'Cadenas', 'Aretes', 'Anillos'], start=1):
            categorias[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={'orden': i, 'activa': True}
            )

        creados = 0
        if not Producto.objects.exists():
            for nombre, cat, precio, stock, oro, k, peso, talla, elab, img in PRODUCTOS_DEMO:
                producto = Producto(
                    nombre=nombre, categoria=categorias[cat], precio=Decimal(precio), stock=stock,
                    tipo_oro=oro, quilates=k, peso_gramos=Decimal(peso), talla_cm=Decimal(talla),
                    elaboracion=elab,
                    descripcion=f'{nombre}: pieza GoldBracelets elaborada con acabados de lujo, '
                                'ideal para uso diario o para regalar.',
                )
                ruta = IMAGENES / img if img else None
                if ruta and ruta.exists():
                    with ruta.open('rb') as archivo:
                        producto.imagen.save(img, File(archivo), save=False)
                producto.save()
                creados += 1

        self.stdout.write(self.style.SUCCESS('Datos iniciales listos.'))
        self.stdout.write('  Admin   -> usuario: admin    (panel /admin/ingresar)')
        self.stdout.write('  Cliente -> usuario: cliente  (tienda /ingresar)')
        self.stdout.write(f'  Productos de ejemplo creados: {creados} (total: {Producto.objects.count()})')
