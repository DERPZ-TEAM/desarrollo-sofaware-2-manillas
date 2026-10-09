from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from account.models import Categoria, Perfil, Producto

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea administrador, cliente demo y categorías iniciales.'

    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@goldbracelets.com',
                'first_name': 'Ana',
                'last_name': 'Gestión',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('AdminGold123')
            admin.save()
        else:
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password('AdminGold123')
            admin.save()
        perfil, _ = Perfil.objects.get_or_create(usuario=admin)
        perfil.rol = Perfil.ROL_ADMIN
        perfil.save()

        cliente, created = User.objects.get_or_create(
            username='cliente',
            defaults={
                'email': 'cliente@goldbracelets.com',
                'first_name': 'Laura',
                'last_name': 'Pérez',
            },
        )
        if created:
            cliente.set_password('Cliente123')
            cliente.save()
        Perfil.objects.get_or_create(usuario=cliente, defaults={'rol': Perfil.ROL_CLIENTE})

        for i, nombre in enumerate(['Pulseras tejidas', 'Aretes', 'Cadenas', 'Anillos', 'Topos'], start=1):
            Categoria.objects.get_or_create(nombre=nombre, defaults={'orden': i, 'activa': True})

        self.stdout.write(self.style.SUCCESS(
            'Listo. Admin: admin / AdminGold123  |  Cliente: cliente / Cliente123'
        ))
        self.stdout.write(f'Productos actuales: {Producto.objects.count()}')
