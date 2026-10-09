from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido, Perfil
from .permissions import EsAdministrador
from .serializers import (
    ActualizarPerfilSerializer,
    CarritoSerializer,
    CategoriaSerializer,
    ItemCarritoSerializer,
    LoginSerializer,
    PedidoSerializer,
    ProductoListSerializer,
    ProductoWriteSerializer,
    RegistroSerializer,
    UsuarioSerializer,
)

User = get_user_model()


def tokens_para(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UsuarioSerializer(user).data,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def registro_view(request):
    serializer = RegistroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(tokens_para(user), status=status.HTTP_201_CREATED)


def _login(request, solo_admin=False):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request,
        username=serializer.validated_data['username'],
        password=serializer.validated_data['password'],
    )
    if user is None:
        return Response(
            {'detail': 'Usuario o contraseña incorrectos.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not user.is_active:
        return Response(
            {'detail': 'Esta cuenta está desactivada.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if solo_admin and not user.is_staff:
        return Response(
            {'detail': 'Esta cuenta no tiene acceso de administrador.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    if not solo_admin and user.is_staff:
        return Response(
            {
                'detail': 'Las cuentas de administrador ingresan por el panel de gestión.',
                'admin': True,
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(tokens_para(user))


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    return _login(request, solo_admin=False)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_view(request):
    return _login(request, solo_admin=True)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def me_view(request):
    if request.method == 'GET':
        return Response(UsuarioSerializer(request.user).data)

    serializer = ActualizarPerfilSerializer(
        data=request.data, context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    user = request.user
    user.first_name = serializer.validated_data['first_name'].strip().title()
    user.last_name = serializer.validated_data['last_name'].strip().title()
    user.email = serializer.validated_data['email']
    user.save()
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    perfil.telefono = serializer.validated_data.get('telefono', '')
    perfil.save()
    return Response(UsuarioSerializer(user).data)


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [EsAdministrador()]

    def get_queryset(self):
        qs = Categoria.objects.annotate(total_productos=Count('productos'))
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(activa=True)
        return qs


class ProductoViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [EsAdministrador()]

    def get_queryset(self):
        qs = Producto.objects.select_related('categoria')
        user = self.request.user
        es_admin = user.is_authenticated and user.is_staff
        if not es_admin:
            qs = qs.filter(activo=True).filter(
                Q(categoria__isnull=True) | Q(categoria__activa=True)
            )
        categoria = self.request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria_id=categoria)
        busqueda = self.request.query_params.get('q')
        if busqueda:
            qs = qs.filter(nombre__icontains=busqueda)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductoWriteSerializer
        return ProductoListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save()
        return Response(
            ProductoListSerializer(producto, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save()
        return Response(ProductoListSerializer(producto, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def visibilidad(self, request, pk=None):
        producto = self.get_object()
        producto.activo = not producto.activo
        producto.save(update_fields=['activo'])
        return Response(ProductoListSerializer(producto, context={'request': request}).data)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def carrito_view(request):
    if request.user.is_staff:
        return Response(
            {'detail': 'El administrador gestiona el catálogo, no el carrito de compra.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    if request.method == 'GET':
        carrito = Carrito.objects.prefetch_related('items__producto__categoria').get(pk=carrito.pk)
        return Response(CarritoSerializer(carrito, context={'request': request}).data)

    if request.method == 'DELETE':
        carrito.items.all().delete()
        return Response(CarritoSerializer(carrito, context={'request': request}).data)

    serializer = ItemCarritoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    producto = Producto.objects.get(pk=serializer.validated_data['producto_id'], activo=True)
    cantidad = serializer.validated_data.get('cantidad', 1)
    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': cantidad},
    )
    if not created:
        item.cantidad = F('cantidad') + cantidad
        item.save()
        item.refresh_from_db()
    if producto.stock and item.cantidad > producto.stock:
        item.cantidad = producto.stock
        item.save()
        return Response(
            {'detail': 'Ajustamos la cantidad al stock disponible.',
             'carrito': CarritoSerializer(
                 Carrito.objects.prefetch_related('items__producto').get(pk=carrito.pk),
                 context={'request': request},
             ).data},
            status=status.HTTP_200_OK,
        )
    carrito = Carrito.objects.prefetch_related('items__producto').get(pk=carrito.pk)
    return Response(CarritoSerializer(carrito, context={'request': request}).data)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def item_carrito_view(request, item_id):
    item = ItemCarrito.objects.filter(
        id=item_id, carrito__usuario=request.user
    ).select_related('carrito', 'producto').first()
    if not item:
        return Response({'detail': 'El artículo no está en tu carrito.'}, status=404)

    if request.method == 'DELETE':
        carrito = item.carrito
        item.delete()
        return Response(CarritoSerializer(
            Carrito.objects.prefetch_related('items__producto').get(pk=carrito.pk),
            context={'request': request},
        ).data)

    cantidad = request.data.get('cantidad')
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        return Response({'detail': 'Cantidad inválida.'}, status=400)
    if cantidad < 1:
        carrito = item.carrito
        item.delete()
    else:
        if item.producto.stock and cantidad > item.producto.stock:
            cantidad = item.producto.stock
        item.cantidad = cantidad
        item.save()
        carrito = item.carrito
    return Response(CarritoSerializer(
        Carrito.objects.prefetch_related('items__producto').get(pk=carrito.pk),
        context={'request': request},
    ).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_view(request):
    if request.user.is_staff:
        return Response({'detail': 'No disponible para administradores.'}, status=403)
    carrito = Carrito.objects.filter(usuario=request.user).prefetch_related('items__producto').first()
    if not carrito or not carrito.items.exists():
        return Response({'detail': 'Tu carrito está vacío.'}, status=400)

    with transaction.atomic():
        items = list(carrito.items.select_related('producto').select_for_update())
        total = 0
        for item in items:
            if not item.producto.activo:
                return Response(
                    {'detail': f'{item.producto.nombre} ya no está disponible.'},
                    status=400,
                )
            if item.producto.stock < item.cantidad:
                return Response(
                    {'detail': f'Stock insuficiente de {item.producto.nombre}.'},
                    status=400,
                )
            total += item.producto.precio * item.cantidad

        pedido = Pedido.objects.create(usuario=request.user, total=total, estado=Pedido.CONFIRMADO)
        for item in items:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                nombre=item.producto.nombre,
                precio=item.producto.precio,
                cantidad=item.cantidad,
            )
            Producto.objects.filter(pk=item.producto.pk).update(
                stock=F('stock') - item.cantidad
            )
        carrito.items.all().delete()

    return Response(PedidoSerializer(pedido).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_pedidos_view(request):
    pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related('items')
    return Response(PedidoSerializer(pedidos, many=True).data)


class PedidoAdminViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [EsAdministrador]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return Pedido.objects.select_related('usuario').prefetch_related('items')


@api_view(['GET'])
@permission_classes([EsAdministrador])
def dashboard_view(request):
    return Response({
        'productos': Producto.objects.count(),
        'productos_visibles': Producto.objects.filter(activo=True).count(),
        'categorias': Categoria.objects.count(),
        'clientes': User.objects.filter(is_staff=False).count(),
        'pedidos': Pedido.objects.count(),
        'ventas': Pedido.objects.exclude(estado=Pedido.CANCELADO).aggregate(
            total=Sum('total')
        )['total'] or 0,
        'pedidos_recientes': PedidoSerializer(
            Pedido.objects.select_related('usuario').prefetch_related('items')[:6],
            many=True,
        ).data,
    })


@api_view(['GET'])
@permission_classes([EsAdministrador])
def clientes_admin_view(request):
    users = User.objects.filter(is_staff=False).select_related('perfil').order_by('-date_joined')
    return Response(UsuarioSerializer(users, many=True).data)
