"""
Vistas del ADMINISTRADOR: escritorio, pedidos, clientes, inventario y reportes.

Todas usan el permiso EsAdministrador: si un cliente (o alguien sin token)
intenta entrar, la API responde 401/403 y no ejecuta nada.
"""
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .. import services
from ..exceptions import ErrorDeNegocio
from ..models import Categoria, ItemPedido, Pedido, Producto
from ..permissions import EsAdministrador
from ..serializers import (
    ClienteAdminSerializer,
    PedidoAdminUpdateSerializer,
    PedidoSerializer,
    ProductoListSerializer,
)

User = get_user_model()
CERO = Value(0, output_field=DecimalField(max_digits=14, decimal_places=2))


def _ventas_validas():
    """Pedidos que cuentan como venta: todos menos los cancelados."""
    return Pedido.objects.exclude(estado=Pedido.CANCELADO)


def _rango_fechas(request, dias_por_defecto=30):
    """Lee ?desde=AAAA-MM-DD&hasta=AAAA-MM-DD y valida el rango (HU-RE-045)."""
    hoy = timezone.localdate()
    try:
        desde = date.fromisoformat(request.query_params['desde']) if request.query_params.get('desde') \
            else hoy - timedelta(days=dias_por_defecto)
        hasta = date.fromisoformat(request.query_params['hasta']) if request.query_params.get('hasta') else hoy
    except ValueError:
        raise ErrorDeNegocio('Las fechas deben tener el formato AAAA-MM-DD.')
    if desde > hasta:
        raise ErrorDeNegocio('La fecha inicial no puede ser mayor que la fecha final.')
    zona = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(desde, time.min), zona)
    fin = timezone.make_aware(datetime.combine(hasta, time.max), zona)
    return desde, hasta, inicio, fin


# ---------------------------------------------------------------------------
# Escritorio (dashboard)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([EsAdministrador])
def dashboard_view(request):
    """GET /api/admin/dashboard/ -> números clave + alertas de bajo stock (HU-IN-048)"""
    ventas = _ventas_validas()
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    alertas = Producto.objects.filter(stock__lte=F('stock_minimo')).select_related('categoria').order_by('stock')
    return Response({
        'productos': Producto.objects.count(),
        'productos_visibles': Producto.objects.filter(activo=True).count(),
        'categorias': Categoria.objects.count(),
        'clientes': User.objects.filter(is_staff=False).count(),
        'pedidos': Pedido.objects.count(),
        'pedidos_pendientes': Pedido.objects.filter(estado=Pedido.PENDIENTE).count(),
        'ventas': ventas.aggregate(t=Coalesce(Sum('total'), CERO))['t'],
        'ventas_mes': ventas.filter(creado__date__gte=inicio_mes).aggregate(t=Coalesce(Sum('total'), CERO))['t'],
        'unidades_en_inventario': Producto.objects.aggregate(t=Coalesce(Sum('stock'), 0))['t'],
        'alertas_stock': ProductoListSerializer(alertas[:10], many=True, context={'request': request}).data,
        'pedidos_recientes': PedidoSerializer(
            Pedido.objects.select_related('usuario').prefetch_related('items')[:6], many=True,
        ).data,
    })


# ---------------------------------------------------------------------------
# Pedidos (HU-PE-024, HU-PE-025, HU-PE-050, HU-IN-029)
# ---------------------------------------------------------------------------
class PedidoAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/admin/pedidos/?estado=pendiente&q=laura -> historial con filtros
    GET   /api/admin/pedidos/{id}/                      -> detalle
    PATCH /api/admin/pedidos/{id}/ {estado, numero_guia, transportadora}
    (No hay DELETE: las ventas no se borran, se cancelan.)
    """
    serializer_class = PedidoSerializer
    permission_classes = [EsAdministrador]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = Pedido.objects.select_related('usuario').prefetch_related('items')
        p = self.request.query_params
        if p.get('estado'):
            qs = qs.filter(estado=p['estado'])
        if p.get('q'):
            q = p['q'].strip()
            filtro = Q(usuario__username__icontains=q) | Q(usuario__email__icontains=q) | \
                Q(nombre_destinatario__icontains=q)
            if q.isdigit():
                filtro |= Q(pk=int(q))
            qs = qs.filter(filtro)
        return qs

    def partial_update(self, request, *args, **kwargs):
        pedido = self.get_object()
        serializer = PedidoAdminUpdateSerializer(pedido, data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        # Primero guardamos la guía (si viene), luego validamos el cambio de estado
        cambios = [c for c in ('transportadora', 'numero_guia') if c in datos]
        for campo in cambios:
            setattr(pedido, campo, datos[campo].strip())
        if cambios:
            pedido.save(update_fields=cambios + ['actualizado'])
        if 'estado' in datos:
            services.cambiar_estado_pedido(pedido, datos['estado'])

        pedido = self.get_queryset().get(pk=pedido.pk)
        respuesta = PedidoSerializer(pedido).data
        respuesta['detail'] = f'Pedido #{pedido.id} actualizado.'
        return Response(respuesta)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Clientes (HU-US-005)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([EsAdministrador])
def clientes_admin_view(request):
    """GET /api/admin/clientes/?q=texto -> clientes en orden alfabético"""
    qs = User.objects.filter(is_staff=False).select_related('perfil').annotate(
        total_pedidos=Count('pedidos', distinct=True),
        total_comprado=Coalesce(
            Sum('pedidos__total', filter=~Q(pedidos__estado=Pedido.CANCELADO)), CERO
        ),
    )
    q = (request.query_params.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q))
    qs = qs.order_by('first_name', 'last_name', 'username')
    return Response(ClienteAdminSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# Inventario (HU-IN-028, HU-IN-048)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([EsAdministrador])
def inventario_view(request):
    """GET /api/admin/inventario/?estado=bajo|agotado|ok"""
    qs = Producto.objects.select_related('categoria').order_by('stock', 'nombre')
    estado = request.query_params.get('estado')
    if estado == 'agotado':
        qs = qs.filter(stock=0)
    elif estado == 'bajo':
        qs = qs.filter(stock__gt=0, stock__lte=F('stock_minimo'))
    elif estado == 'ok':
        qs = qs.filter(stock__gt=F('stock_minimo'))
    resumen = Producto.objects.aggregate(
        unidades=Coalesce(Sum('stock'), 0),
        valor=Coalesce(Sum(F('stock') * F('precio'), output_field=DecimalField(max_digits=16, decimal_places=2)), CERO),
        agotados=Count('id', filter=Q(stock=0)),
        bajos=Count('id', filter=Q(stock__gt=0, stock__lte=F('stock_minimo'))),
    )
    return Response({
        'resumen': resumen,
        'productos': ProductoListSerializer(qs, many=True, context={'request': request}).data,
    })


# ---------------------------------------------------------------------------
# Reportes (HU-RE-030, HU-RE-031, HU-RE-045, HU-RE-046)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([EsAdministrador])
def reporte_ingresos_view(request):
    """GET /api/admin/reportes/ingresos/?periodo=dia|mes|anio&desde=&hasta="""
    periodo = request.query_params.get('periodo', 'dia')
    truncar = {'dia': TruncDay, 'mes': TruncMonth, 'anio': TruncYear}.get(periodo)
    if truncar is None:
        raise ErrorDeNegocio('El periodo debe ser dia, mes o anio.')
    desde, hasta, inicio, fin = _rango_fechas(request, dias_por_defecto=365 if periodo != 'dia' else 30)

    filas = (
        _ventas_validas().filter(creado__range=(inicio, fin))
        .annotate(periodo=truncar('creado'))
        .values('periodo')
        .annotate(ingresos=Sum('total'), pedidos=Count('id'), descuentos=Sum('descuento'))
        .order_by('periodo')
    )
    formato = {'dia': '%Y-%m-%d', 'mes': '%Y-%m', 'anio': '%Y'}[periodo]
    datos = [
        {'periodo': f['periodo'].strftime(formato), 'ingresos': f['ingresos'],
         'pedidos': f['pedidos'], 'descuentos': f['descuentos']}
        for f in filas
    ]
    return Response({
        'periodo': periodo, 'desde': desde, 'hasta': hasta,
        'total_ingresos': sum((d['ingresos'] for d in datos), 0),
        'total_pedidos': sum(d['pedidos'] for d in datos),
        'filas': datos,
    })


@api_view(['GET'])
@permission_classes([EsAdministrador])
def reporte_mas_vendidos_view(request):
    """GET /api/admin/reportes/mas-vendidos/?criterio=cantidad|ingresos&categoria=&limite=10"""
    criterio = request.query_params.get('criterio', 'cantidad')
    if criterio not in ('cantidad', 'ingresos'):
        raise ErrorDeNegocio('El criterio debe ser "cantidad" o "ingresos".')
    try:
        limite = max(1, min(int(request.query_params.get('limite', 10)), 50))
    except ValueError:
        raise ErrorDeNegocio('El límite debe ser un número.')
    desde, hasta, inicio, fin = _rango_fechas(request, dias_por_defecto=365)

    qs = ItemPedido.objects.filter(
        pedido__creado__range=(inicio, fin),
    ).exclude(pedido__estado=Pedido.CANCELADO)
    if request.query_params.get('categoria'):
        qs = qs.filter(producto__categoria_id=request.query_params['categoria'])
    filas = (
        qs.values('producto_id', 'nombre', 'producto__categoria__nombre')
        .annotate(
            unidades=Sum('cantidad'),
            ingresos=Sum(F('precio') * F('cantidad'), output_field=DecimalField(max_digits=16, decimal_places=2)),
        )
        .order_by('-unidades' if criterio == 'cantidad' else '-ingresos')[:limite]
    )
    return Response({
        'criterio': criterio, 'desde': desde, 'hasta': hasta,
        'filas': [
            {'producto_id': f['producto_id'], 'nombre': f['nombre'],
             'categoria': f['producto__categoria__nombre'], 'unidades': f['unidades'], 'ingresos': f['ingresos']}
            for f in filas
        ],
    })


@api_view(['GET'])
@permission_classes([EsAdministrador])
def reporte_sin_ventas_view(request):
    """GET /api/admin/reportes/sin-ventas/?desde=&hasta= -> productos sin movimiento"""
    desde, hasta, inicio, fin = _rango_fechas(request, dias_por_defecto=30)
    vendidos = ItemPedido.objects.filter(
        pedido__creado__range=(inicio, fin), producto__isnull=False,
    ).exclude(pedido__estado=Pedido.CANCELADO).values('producto_id')
    qs = Producto.objects.exclude(pk__in=vendidos).select_related('categoria').order_by('creado')
    return Response({
        'desde': desde, 'hasta': hasta,
        'productos': ProductoListSerializer(qs, many=True, context={'request': request}).data,
    })
