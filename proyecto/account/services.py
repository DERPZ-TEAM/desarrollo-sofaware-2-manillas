"""
Servicios = LÓGICA DEL NEGOCIO.

Las vistas (views/) solo reciben la petición y devuelven la respuesta.
Las reglas importantes (stock, descuentos, estados del pedido) viven aquí,
en un solo lugar, para que sean fáciles de probar y de explicar.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import F

from .exceptions import ErrorDeNegocio
from .models import Carrito, ItemCarrito, ItemPedido, Pedido, Producto

# Descuento por volumen para mayoristas (Especificación inicial, requisito 27):
# (cantidad mínima de piezas, porcentaje de descuento). Se revisa de mayor a menor.
DESCUENTOS_POR_VOLUMEN = (
    (24, Decimal('15')),
    (12, Decimal('10')),
    (6, Decimal('5')),
)


def porcentaje_descuento(cantidad_total):
    for minimo, porcentaje in DESCUENTOS_POR_VOLUMEN:
        if cantidad_total >= minimo:
            return porcentaje
    return Decimal('0')


def calcular_totales(lineas):
    """Recibe [(precio, cantidad), ...] y devuelve subtotal, descuento, total.

    Ejemplo: 6 pulseras de $100.000 -> subtotal 600.000, 5% = 30.000, total 570.000
    """
    subtotal = sum((Decimal(precio) * cantidad for precio, cantidad in lineas), Decimal('0'))
    piezas = sum(cantidad for _, cantidad in lineas)
    porcentaje = porcentaje_descuento(piezas)
    descuento = (subtotal * porcentaje / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return {
        'subtotal': subtotal,
        'piezas': piezas,
        'porcentaje_descuento': porcentaje,
        'descuento': descuento,
        'total': subtotal - descuento,
    }


# ---------------------------------------------------------------------------
# Carrito (HU-CO-016, HU-CO-017, HU-CO-018, HU-IN-027)
# ---------------------------------------------------------------------------
def obtener_carrito(usuario):
    carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
    return carrito


def agregar_al_carrito(usuario, producto_id, cantidad=1):
    """Suma 'cantidad' unidades del producto al carrito validando el stock.

    Devuelve (carrito, aviso). 'aviso' es un texto si hubo que ajustar algo.
    """
    if cantidad < 1:
        raise ErrorDeNegocio('La cantidad mínima es 1.')

    producto = Producto.objects.filter(pk=producto_id, activo=True).first()
    if producto is None:
        raise ErrorDeNegocio('El producto no está disponible.', 404)
    if producto.stock == 0:
        raise ErrorDeNegocio(f'"{producto.nombre}" está agotado por ahora.')

    carrito = obtener_carrito(usuario)
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito, producto=producto, defaults={'cantidad': 0}
    )
    deseado = item.cantidad + cantidad
    aviso = None
    if deseado > producto.stock:
        deseado = producto.stock
        aviso = f'Solo hay {producto.stock} unidades de "{producto.nombre}". Ajustamos la cantidad.'
    item.cantidad = deseado
    item.save(update_fields=['cantidad'])
    carrito.save(update_fields=['actualizado'])
    return carrito, aviso


def cambiar_cantidad_item(usuario, item_id, cantidad):
    item = (
        ItemCarrito.objects.select_related('producto', 'carrito')
        .filter(pk=item_id, carrito__usuario=usuario)
        .first()
    )
    if item is None:
        raise ErrorDeNegocio('El artículo no está en tu carrito.', 404)
    carrito = item.carrito
    if cantidad < 1:
        item.delete()
        return carrito, None
    aviso = None
    if cantidad > item.producto.stock:
        cantidad = item.producto.stock
        aviso = f'Solo hay {item.producto.stock} unidades disponibles.'
        if cantidad == 0:
            item.delete()
            return carrito, 'El producto se agotó y lo quitamos de tu carrito.'
    item.cantidad = cantidad
    item.save(update_fields=['cantidad'])
    return carrito, aviso


def quitar_item(usuario, item_id):
    eliminados, _ = ItemCarrito.objects.filter(pk=item_id, carrito__usuario=usuario).delete()
    if not eliminados:
        raise ErrorDeNegocio('El producto ya no existe en tu carrito.', 404)
    return obtener_carrito(usuario)


# ---------------------------------------------------------------------------
# Checkout = convertir el carrito en un pedido (HU-VE-019..022, HU-IN-026)
# ---------------------------------------------------------------------------
@transaction.atomic
def crear_pedido_desde_carrito(usuario, datos_envio):
    """Crea el pedido de forma ATÓMICA: o se hace todo, o no se hace nada.

    Pasos:
      1. Bloquea (SELECT ... FOR UPDATE) las filas de los productos del carrito,
         para que dos clientes no compren la última unidad al mismo tiempo.
      2. Valida que cada producto siga activo y tenga stock suficiente.
      3. Calcula subtotal, descuento por volumen y total.
      4. Crea el Pedido y sus ItemPedido (con el precio congelado).
      5. Descuenta el stock y vacía el carrito.
    Si algo falla, transaction.atomic deshace todos los cambios (ROLLBACK).
    """
    carrito = Carrito.objects.filter(usuario=usuario).first()
    items = list(carrito.items.all()) if carrito else []
    if not items:
        raise ErrorDeNegocio('Tu carrito está vacío.')

    ids = sorted(i.producto_id for i in items)          # orden fijo evita bloqueos cruzados
    productos = {p.id: p for p in Producto.objects.select_for_update().filter(pk__in=ids).order_by('id')}

    lineas = []
    for item in items:
        producto = productos.get(item.producto_id)
        if producto is None or not producto.activo:
            nombre = producto.nombre if producto else 'Un producto'
            raise ErrorDeNegocio(f'{nombre} ya no está disponible. Quítalo del carrito para continuar.')
        if producto.stock < item.cantidad:
            raise ErrorDeNegocio(
                f'Stock insuficiente de "{producto.nombre}": quedan {producto.stock} unidades.'
            )
        lineas.append((producto, item.cantidad))

    totales = calcular_totales([(p.precio, c) for p, c in lineas])
    pedido = Pedido.objects.create(
        usuario=usuario,
        subtotal=totales['subtotal'],
        descuento=totales['descuento'],
        total=totales['total'],
        estado=Pedido.PENDIENTE,
        **datos_envio,
    )
    ItemPedido.objects.bulk_create([
        ItemPedido(pedido=pedido, producto=p, nombre=p.nombre, precio=p.precio, cantidad=c)
        for p, c in lineas
    ])
    for producto, cantidad in lineas:
        # F('stock') hace la resta DENTRO de PostgreSQL: UPDATE producto SET stock = stock - n
        Producto.objects.filter(pk=producto.pk).update(stock=F('stock') - cantidad)
    carrito.items.all().delete()
    return pedido


# ---------------------------------------------------------------------------
# Estados del pedido (HU-PE-024) y devolución de stock al cancelar
# ---------------------------------------------------------------------------
@transaction.atomic
def cambiar_estado_pedido(pedido, nuevo_estado):
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    if nuevo_estado == pedido.estado:
        return pedido
    if not pedido.puede_cambiar_a(nuevo_estado):
        raise ErrorDeNegocio(
            f'No se puede pasar un pedido de "{pedido.get_estado_display()}" '
            f'a "{dict(Pedido.ESTADOS).get(nuevo_estado, nuevo_estado)}".'
        )
    if nuevo_estado == Pedido.CANCELADO:
        # Devolvemos al inventario lo que se había descontado
        for item in pedido.items.filter(producto__isnull=False):
            Producto.objects.filter(pk=item.producto_id).update(stock=F('stock') + item.cantidad)
    pedido.estado = nuevo_estado
    pedido.save(update_fields=['estado', 'actualizado'])
    return pedido
