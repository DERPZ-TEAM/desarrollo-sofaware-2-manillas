"""
Permisos = reglas que deciden QUIÉN puede usar cada ruta de la API.

DRF llama a has_permission() antes de ejecutar la vista. Si devuelve False,
responde automáticamente 401 (no autenticado) o 403 (prohibido).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Perfil


def es_admin(user):
    """Un usuario es administrador si está autenticado y tiene rol 'admin'.

    El rol vive en account_perfil.rol. El campo is_staff de Django se mantiene
    sincronizado con ese rol (ver signals.py) para que también pueda entrar
    al panel /django-admin/.
    """
    if not (user and user.is_authenticated):
        return False
    perfil = getattr(user, 'perfil', None)
    if perfil is not None:
        return perfil.rol == Perfil.ROL_ADMIN
    return user.is_staff


class EsAdministrador(BasePermission):
    message = 'Solo el administrador puede realizar esta acción.'

    def has_permission(self, request, view):
        return es_admin(request.user)


class EsCliente(BasePermission):
    message = 'Esta sección es solo para clientes de la tienda.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not es_admin(user))


class LecturaPublicaEscrituraAdmin(BasePermission):
    """GET es público (catálogo); POST/PUT/PATCH/DELETE solo para el admin."""
    message = 'Solo el administrador puede modificar el catálogo.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return es_admin(request.user)
