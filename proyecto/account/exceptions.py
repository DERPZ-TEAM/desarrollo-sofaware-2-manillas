"""
Manejo GLOBAL de errores de la API.

Sin esto, cada error tendría un formato distinto y algunos (errores de
programación, base de datos caída) devolverían una página HTML enorme.
Con este manejador, el frontend SIEMPRE recibe un JSON así:

    {
        "detail": "Mensaje principal para mostrar al usuario",
        "errors": {"campo": ["mensaje del campo"]}   # solo en errores de validación
    }
"""
import logging
import math

from django.db import DatabaseError, IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('goldbracelets.api')


class ErrorDeNegocio(Exception):
    """Error esperado de una regla del negocio (ej. 'stock insuficiente')."""

    def __init__(self, mensaje, codigo=status.HTTP_400_BAD_REQUEST):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _primer_mensaje(errores):
    """Toma el primer mensaje legible de un diccionario/lista de errores."""
    if isinstance(errores, dict):
        for valor in errores.values():
            return _primer_mensaje(valor)
    if isinstance(errores, (list, tuple)) and errores:
        return _primer_mensaje(errores[0])
    return str(errores)


def manejador_global_errores(exc, context):
    if isinstance(exc, ErrorDeNegocio):
        return Response({'detail': exc.mensaje}, status=exc.codigo)

    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'No se puede eliminar: hay registros relacionados (por ejemplo, pedidos).'},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, Http404):
        return Response({'detail': 'El recurso solicitado no existe.'}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, Throttled):
        minutos = max(1, math.ceil((exc.wait or 60) / 60))
        return Response(
            {'detail': f'Demasiados intentos. Espera {minutos} minuto(s) y vuelve a intentarlo.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # Errores que DRF ya sabe manejar (validación, permisos, autenticación...)
    respuesta = exception_handler(exc, context)
    if respuesta is not None:
        if isinstance(exc, ValidationError):
            errores = respuesta.data
            respuesta.data = {'detail': _primer_mensaje(errores), 'errors': errores}
        elif isinstance(respuesta.data, dict) and 'detail' in respuesta.data:
            respuesta.data = {'detail': str(respuesta.data['detail'])}
        return respuesta

    # Errores inesperados: se registran en el log y se responde un 500 limpio
    vista = context.get('view').__class__.__name__ if context.get('view') else '?'
    if isinstance(exc, IntegrityError):
        # La BD rechazó el dato (ej. llave duplicada): no es un problema de conexión
        logger.exception('Error de integridad en %s', vista)
        return Response(
            {'detail': 'No se pudo guardar porque entra en conflicto con un registro existente.'},
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, DatabaseError):
        logger.exception('Error de base de datos en %s', vista)
        return Response(
            {'detail': 'Error de conexión con la base de datos. Intenta de nuevo.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if isinstance(exc, OSError):
        logger.exception('Error de archivos/almacenamiento en %s', vista)
        return Response({'detail': str(exc) or 'Error al guardar el archivo.'}, status=status.HTTP_502_BAD_GATEWAY)

    logger.exception('Error inesperado en %s', vista)
    return Response(
        {'detail': 'Ocurrió un error inesperado en el servidor.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
