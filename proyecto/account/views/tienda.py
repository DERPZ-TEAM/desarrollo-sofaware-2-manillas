"""
Vistas del CLIENTE: carrito, checkout y "mis pedidos".

Todas usan el permiso EsCliente: un administrador no puede comprar
(los dos flujos de usuario son independientes).
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .. import services
from ..exceptions import ErrorDeNegocio
from ..models import Pedido, Perfil
from ..permissions import EsCliente
from ..serializers import (
    AgregarAlCarritoSerializer,
    CarritoSerializer,
    CheckoutSerializer,
    PedidoSerializer,
)


def _carrito_json(request, carrito, aviso=None, codigo=status.HTTP_200_OK, advertencia=False):
    datos = CarritoSerializer(carrito, context={'request': request}).data
    if aviso:
        datos['detail'] = aviso
        datos['advertencia'] = advertencia   # True = se ajustó algo (ej. cantidad al stock)
    return Response(datos, status=codigo)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([EsCliente])
def carrito_view(request):
    """
    GET    /api/carrito/   -> ver carrito con totales (HU-CO-018)
    POST   /api/carrito/   -> agregar producto {producto_id, cantidad} (HU-CO-016)
    DELETE /api/carrito/   -> vaciar carrito
    """
    if request.method == 'GET':
        return _carrito_json(request, services.obtener_carrito(request.user))

    if request.method == 'DELETE':
        carrito = services.obtener_carrito(request.user)
        carrito.items.all().delete()
        return _carrito_json(request, carrito, 'Vaciamos tu carrito.')

    serializer = AgregarAlCarritoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    carrito, aviso = services.agregar_al_carrito(
        request.user, serializer.validated_data['producto_id'], serializer.validated_data['cantidad']
    )
    return _carrito_json(request, carrito, aviso or 'Producto agregado al carrito.', advertencia=bool(aviso))


@api_view(['PATCH', 'DELETE'])
@permission_classes([EsCliente])
def item_carrito_view(request, item_id):
    """
    PATCH  /api/carrito/items/{id}/ {cantidad}  -> cambiar cantidad
    DELETE /api/carrito/items/{id}/             -> quitar (HU-CO-017)
    """
    if request.method == 'DELETE':
        carrito = services.quitar_item(request.user, item_id)
        return _carrito_json(request, carrito, 'Producto eliminado del carrito.')

    try:
        cantidad = int(request.data.get('cantidad'))
    except (TypeError, ValueError):
        raise ErrorDeNegocio('Cantidad inválida.')
    carrito, aviso = services.cambiar_cantidad_item(request.user, item_id, cantidad)
    return _carrito_json(request, carrito, aviso, advertencia=bool(aviso))


@api_view(['POST'])
@permission_classes([EsCliente])
def checkout_view(request):
    """POST /api/checkout/ -> confirma la compra (HU-VE-019, 020, 021, 022)"""
    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    datos = dict(serializer.validated_data)
    guardar = datos.pop('guardar_direccion', True)

    pedido = services.crear_pedido_desde_carrito(request.user, datos)

    if guardar:   # recordamos la dirección para la próxima compra
        Perfil.objects.filter(usuario=request.user).update(
            direccion=datos['direccion_envio'], ciudad=datos['ciudad'], departamento=datos['departamento'],
        )
    respuesta = PedidoSerializer(pedido).data
    respuesta['detail'] = f'¡Compra confirmada! Tu pedido es el #{pedido.id}.'
    return Response(respuesta, status=status.HTTP_201_CREATED)


def _mis_pedidos(request):
    return Pedido.objects.filter(usuario=request.user).select_related('usuario').prefetch_related('items')


@api_view(['GET'])
@permission_classes([EsCliente])
def mis_pedidos_view(request):
    """GET /api/pedidos/ -> historial del cliente con su estado (HU-PE-023)"""
    return Response(PedidoSerializer(_mis_pedidos(request), many=True).data)


@api_view(['GET'])
@permission_classes([EsCliente])
def mi_pedido_detalle_view(request, pedido_id):
    """GET /api/pedidos/{id}/ -> comprobante de compra (HU-VE-022)"""
    pedido = _mis_pedidos(request).filter(pk=pedido_id).first()
    if pedido is None:
        raise ErrorDeNegocio('El pedido no existe.', 404)
    return Response(PedidoSerializer(pedido).data)


@api_view(['POST'])
@permission_classes([EsCliente])
def cancelar_mi_pedido_view(request, pedido_id):
    """POST /api/pedidos/{id}/cancelar/ -> el cliente cancela si aún no fue enviado"""
    pedido = _mis_pedidos(request).filter(pk=pedido_id).first()
    if pedido is None:
        raise ErrorDeNegocio('El pedido no existe.', 404)
    pedido = services.cambiar_estado_pedido(pedido, Pedido.CANCELADO)
    datos = PedidoSerializer(Pedido.objects.prefetch_related('items').get(pk=pedido.pk)).data
    datos['detail'] = 'Pedido cancelado. Devolvimos las piezas al inventario.'
    return Response(datos)

