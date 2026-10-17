"""
Las vistas están separadas por responsabilidad:
    auth.py      -> registro, login, perfil, recuperación de contraseña
    catalogo.py  -> categorías y productos (público para leer, admin para editar)
    tienda.py    -> carrito, checkout y pedidos del cliente
    admin.py     -> panel del administrador y reportes
"""
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def salud_view(request):
    """GET /api/salud/ -> usado por Render para saber si el servidor está vivo."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        base_de_datos = 'ok'
    except Exception:  # noqa: BLE001
        base_de_datos = 'sin conexión'
    return Response({'estado': 'ok', 'base_de_datos': base_de_datos, 'api': '/api/'})
