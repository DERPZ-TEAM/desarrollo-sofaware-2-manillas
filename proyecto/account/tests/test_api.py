"""
Pruebas automáticas de la API.  Ejecutar con:

    python manage.py test account

Django crea una base de datos de prueba vacía, ejecuta cada prueba y la borra.
"""
import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from account.models import Categoria, Pedido, Producto
from account.services import calcular_totales

User = get_user_model()
MEDIA_TEMPORAL = tempfile.mkdtemp()


def imagen_png(nombre='foto.png'):
    buffer = BytesIO()
    Image.new('RGB', (10, 10), 'gold').save(buffer, 'PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL, SUPABASE_URL='')
class BaseAPITest(APITestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        cache.clear()   # reinicia el contador del límite de intentos de login
        Producto.objects.all().delete()   # en PostgreSQL la migración 0008 carga el catálogo demo
        self.admin = User.objects.create_user('admin', 'admin@gb.com', 'AdminGold123', is_staff=True)
        self.cliente = User.objects.create_user('laura', 'laura@gb.com', 'Cliente123', first_name='Laura')
        self.cat = Categoria.objects.create(nombre='Pulseras')
        self.prod = Producto.objects.create(
            nombre='Pulsera Imperial', descripcion='Pulsera tejida en oro 18k',
            precio=Decimal('100000'), stock=10, categoria=self.cat, tipo_oro='amarillo',
        )

    def login(self, usuario, clave, admin=False):
        url = '/api/auth/admin/login/' if admin else '/api/auth/login/'
        r = self.client.post(url, {'username': usuario, 'password': clave}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
        return r.data


class AutenticacionTests(BaseAPITest):

    def test_registro_crea_cliente_con_rol(self):
        r = self.client.post('/api/auth/registro/', {
            'username': 'nuevo_user', 'email': 'nuevo@gb.com', 'primer_nombre': 'ana',
            'apellidos': 'gómez', 'password': 'Segura2026x', 'password2': 'Segura2026x',
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['user']['rol'], 'cliente')
        self.assertEqual(r.data['user']['first_name'], 'Ana')

    def test_registro_con_campos_vacios_muestra_errores(self):
        r = self.client.post('/api/auth/registro/', {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('errors', r.data)
        self.assertIn('username', r.data['errors'])

    def test_login_con_correo(self):
        datos = self.login('laura@gb.com', 'Cliente123')
        self.assertEqual(datos['user']['username'], 'laura')

    def test_login_incorrecto(self):
        r = self.client.post('/api/auth/login/', {'username': 'laura', 'password': 'mala'}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_flujos_separados_admin_y_cliente(self):
        r = self.client.post('/api/auth/login/', {'username': 'admin', 'password': 'AdminGold123'}, format='json')
        self.assertEqual(r.status_code, 403)
        r = self.client.post('/api/auth/admin/login/', {'username': 'laura', 'password': 'Cliente123'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_logout_invalida_refresh(self):
        datos = self.login('laura', 'Cliente123')
        r = self.client.post('/api/auth/logout/', {'refresh': datos['refresh']}, format='json')
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/api/auth/refresh/', {'refresh': datos['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_recuperar_password(self):
        r = self.client.post('/api/auth/password/recuperar/', {'email': 'noexiste@gb.com'}, format='json')
        self.assertEqual(r.status_code, 404)
        with self.settings(MOSTRAR_ENLACE_RECUPERACION=True):
            r = self.client.post('/api/auth/password/recuperar/', {'email': 'laura@gb.com'}, format='json')
        self.assertEqual(r.status_code, 200)
        uid, token = r.data['enlace_demo'].rstrip('/').split('/')[-2:]
        r = self.client.post('/api/auth/password/restablecer/', {
            'uid': uid, 'token': token, 'password': 'NuevaClave2026', 'password2': 'NuevaClave2026',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.login('laura', 'NuevaClave2026')

    def test_actualizar_perfil(self):
        self.login('laura', 'Cliente123')
        r = self.client.put('/api/auth/me/', {
            'first_name': 'laura', 'last_name': 'pérez', 'email': 'laura@gb.com',
            'telefono': '3001234567', 'ciudad': 'Cali',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['telefono'], '3001234567')
        self.assertEqual(r.data['ciudad'], 'Cali')


class PermisosTests(BaseAPITest):

    def test_catalogo_es_publico(self):
        r = self.client.get('/api/productos/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_cliente_no_puede_crear_productos(self):
        self.login('laura', 'Cliente123')
        r = self.client.post('/api/productos/', {'nombre': 'X'}, format='json')
        self.assertEqual(r.status_code, 403)

    def test_anonimo_no_ve_panel_admin(self):
        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 401)

    def test_admin_no_puede_comprar(self):
        self.login('admin', 'AdminGold123', admin=True)
        self.assertEqual(self.client.get('/api/carrito/').status_code, 403)


class CrudProductosTests(BaseAPITest):

    def test_crud_completo_con_imagen(self):
        self.login('admin', 'AdminGold123', admin=True)
        r = self.client.post('/api/productos/', {
            'nombre': 'Brazalete Luna', 'descripcion': 'Brazalete de oro blanco 18k',
            'precio': '250000', 'stock': '5', 'categoria': self.cat.id, 'activo': 'true',
            'tipo_oro': 'blanco', 'quilates': '18', 'peso_gramos': '', 'imagen': imagen_png(),
        }, format='multipart')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data['imagen_url'])
        pid = r.data['id']

        r = self.client.patch(f'/api/productos/{pid}/', {'precio': '260000', 'stock': 7}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(Decimal(r.data['precio']), Decimal('260000'))

        r = self.client.delete(f'/api/productos/{pid}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.delete(f'/api/productos/{pid}/').status_code, 404)

    def test_validaciones_de_producto(self):
        self.login('admin', 'AdminGold123', admin=True)
        r = self.client.post('/api/productos/', {
            'nombre': 'ab', 'descripcion': 'corta', 'precio': '0',
        }, format='json')
        self.assertEqual(r.status_code, 400)
        for campo in ('nombre', 'descripcion', 'precio', 'categoria'):
            self.assertIn(campo, r.data['errors'])

    def test_imagen_con_formato_invalido(self):
        self.login('admin', 'AdminGold123', admin=True)
        archivo = SimpleUploadedFile('virus.exe', b'no soy imagen', content_type='application/octet-stream')
        r = self.client.patch(f'/api/productos/{self.prod.id}/', {'imagen': archivo}, format='multipart')
        self.assertEqual(r.status_code, 400)

    def test_filtros_del_catalogo(self):
        Producto.objects.create(nombre='Cadena Rosa', descripcion='Cadena oro rosa 14k',
                                precio=Decimal('300000'), stock=2, categoria=self.cat, tipo_oro='rosa')
        self.assertEqual(len(self.client.get('/api/productos/?q=cadena').data), 1)
        self.assertEqual(len(self.client.get('/api/productos/?tipo_oro=rosa').data), 1)
        self.assertEqual(len(self.client.get('/api/productos/?precio_min=150000').data), 1)
        r = self.client.get('/api/productos/?precio_min=5&precio_max=1')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.client.get('/api/productos/?tipo_oro=plata').status_code, 400)


class CompraTests(BaseAPITest):
    ENVIO = {
        'nombre_destinatario': 'Laura Pérez', 'telefono_contacto': '3001234567',
        'direccion_envio': 'Calle 10 # 5-20', 'ciudad': 'Cali', 'departamento': 'Valle',
        'metodo_pago': 'contraentrega',
    }

    def test_no_se_agrega_producto_agotado(self):
        self.prod.stock = 0
        self.prod.save()
        self.login('laura', 'Cliente123')
        r = self.client.post('/api/carrito/', {'producto_id': self.prod.id}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cantidad_se_ajusta_al_stock(self):
        self.login('laura', 'Cliente123')
        r = self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 50}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['items'][0]['cantidad'], 10)

    def test_checkout_descuenta_stock_y_aplica_descuento(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 6}, format='json')
        r = self.client.post('/api/checkout/', self.ENVIO, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Decimal(r.data['subtotal']), Decimal('600000'))
        self.assertEqual(Decimal(r.data['descuento']), Decimal('30000'))   # 5% por 6 piezas
        self.assertEqual(Decimal(r.data['total']), Decimal('570000'))
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 4)
        self.assertEqual(self.client.get('/api/carrito/').data['resumen']['cantidad_items'], 0)

    def test_checkout_sin_metodo_de_pago(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id}, format='json')
        datos = dict(self.ENVIO)
        datos.pop('metodo_pago')
        self.assertEqual(self.client.post('/api/checkout/', datos, format='json').status_code, 400)

    def test_checkout_falla_si_otro_compro_el_stock(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 3}, format='json')
        Producto.objects.filter(pk=self.prod.pk).update(stock=1)
        r = self.client.post('/api/checkout/', self.ENVIO, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Pedido.objects.count(), 0)   # no quedó nada a medias

    def test_cancelar_devuelve_stock_y_estados_validos(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 2}, format='json')
        pedido_id = self.client.post('/api/checkout/', self.ENVIO, format='json').data['id']

        self.login('admin', 'AdminGold123', admin=True)
        r = self.client.patch(f'/api/admin/pedidos/{pedido_id}/', {'estado': 'entregado'}, format='json')
        self.assertEqual(r.status_code, 400)   # no se puede saltar de pendiente a entregado
        r = self.client.patch(f'/api/admin/pedidos/{pedido_id}/', {'estado': 'confirmado'}, format='json')
        self.assertEqual(r.status_code, 200)
        r = self.client.patch(f'/api/admin/pedidos/{pedido_id}/', {'estado': 'enviado'}, format='json')
        self.assertEqual(r.status_code, 400)   # falta la guía
        r = self.client.patch(f'/api/admin/pedidos/{pedido_id}/', {'estado': 'cancelado'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 10)

    def test_reportes_e_inventario(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 8}, format='json')
        self.client.post('/api/checkout/', self.ENVIO, format='json')
        self.login('admin', 'AdminGold123', admin=True)
        r = self.client.get('/api/admin/reportes/ingresos/?periodo=mes')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['total_pedidos'], 1)
        r = self.client.get('/api/admin/reportes/mas-vendidos/')
        self.assertEqual(r.data['filas'][0]['unidades'], 8)
        r = self.client.get('/api/admin/dashboard/')
        self.assertEqual(len(r.data['alertas_stock']), 1)   # quedan 2 <= stock mínimo 3
        r = self.client.get('/api/admin/reportes/sin-ventas/?desde=2026-12-01&hasta=2026-01-01')
        self.assertEqual(r.status_code, 400)


class LogicaTests(BaseAPITest):

    def test_tabla_de_descuentos(self):
        self.assertEqual(calcular_totales([(Decimal('10'), 5)])['porcentaje_descuento'], 0)
        self.assertEqual(calcular_totales([(Decimal('10'), 6)])['porcentaje_descuento'], 5)
        self.assertEqual(calcular_totales([(Decimal('10'), 12)])['porcentaje_descuento'], 10)
        self.assertEqual(calcular_totales([(Decimal('10'), 30)])['porcentaje_descuento'], 15)


class PruebaCompletaTests(BaseAPITest):
    """Casos encontrados en la prueba completa de la página (octubre 2026)."""

    def test_filtro_categoria_no_numerica(self):
        r = self.client.get('/api/productos/?categoria=abc')
        self.assertEqual(r.status_code, 400)

    def test_login_usuario_sin_distinguir_mayusculas(self):
        self.login('LAURA', 'Cliente123')

    def test_cambiar_password_cierra_otras_sesiones(self):
        otra_sesion = self.login('laura', 'Cliente123')
        self.login('laura', 'Cliente123')
        r = self.client.post('/api/auth/password/cambiar/', {
            'password_actual': 'Cliente123', 'password': 'NuevaClave2026', 'password2': 'NuevaClave2026',
        }, format='json')
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/api/auth/refresh/', {'refresh': otra_sesion['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_aviso_de_cantidad_ajustada_es_advertencia(self):
        self.login('laura', 'Cliente123')
        r = self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 50}, format='json')
        self.assertTrue(r.data['advertencia'])
        r = self.client.post('/api/carrito/', {'producto_id': self.prod.id, 'cantidad': 0}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_destacados_variados_sin_ventas(self):
        otra = Categoria.objects.create(nombre='Relojes')
        for i in range(3):
            Producto.objects.create(nombre=f'Reloj {i}', descripcion='Reloj de prueba dorado',
                                    precio=Decimal('100'), stock=5, categoria=otra)
        r = self.client.get('/api/productos/destacados/')
        categorias = {p['categoria_nombre'] for p in r.data}
        self.assertEqual(categorias, {'Pulseras', 'Relojes'})

    def test_pendiente_a_enviado_explica_la_transicion(self):
        self.login('laura', 'Cliente123')
        self.client.post('/api/carrito/', {'producto_id': self.prod.id}, format='json')
        pedido = self.client.post('/api/checkout/', CompraTests.ENVIO, format='json').data['id']
        self.login('admin', 'AdminGold123', admin=True)
        r = self.client.patch(f'/api/admin/pedidos/{pedido}/', {'estado': 'enviado'}, format='json')
        self.assertIn('No se puede pasar', r.data['detail'])
