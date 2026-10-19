"""
Vistas del CATÁLOGO: categorías y productos.

Se usan ViewSets de DRF: una sola clase crea automáticamente las 5 rutas
del CRUD (Create, Read, Update, Delete):

    GET    /api/productos/        -> list      (público)
    POST   /api/productos/        -> create    (solo admin)
    GET    /api/productos/{id}/   -> retrieve  (público)
    PATCH  /api/productos/{id}/   -> partial_update (solo admin)
    DELETE /api/productos/{id}/   -> destroy   (solo admin)
"""
from decimal import Decimal, InvalidOperation

from django.db.models import Count, F, Q, Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from ..exceptions import ErrorDeNegocio
from ..models import Categoria, Pedido, Producto
from ..permissions import LecturaPublicaEscrituraAdmin, es_admin
from ..serializers import CategoriaSerializer, ProductoListSerializer, ProductoWriteSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [LecturaPublicaEscrituraAdmin]

    def get_queryset(self):
        qs = Categoria.objects.order_by('nombre')
        if es_admin(self.request.user):
            return qs.annotate(total_productos=Count('productos'))
        # Clientes: solo categorías activas y conteo de productos visibles
        return qs.filter(activa=True).annotate(
            total_productos=Count('productos', filter=Q(productos__activo=True))
        )


def _decimal(valor, nombre):
    try:
        numero = Decimal(valor)
    except (InvalidOperation, TypeError):
        raise ErrorDeNegocio(f'El valor de "{nombre}" no es un número válido.')
    if numero < 0:
        raise ErrorDeNegocio(f'El valor de "{nombre}" no puede ser negativo.')
    return numero


class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [LecturaPublicaEscrituraAdmin]
    parser_classes = [JSONParser, FormParser, MultiPartParser]  # acepta JSON y formularios con imagen

    ORDENES = {
        'recientes': '-creado',
        'precio_asc': 'precio',
        'precio_desc': '-precio',
        'nombre': 'nombre',
        'stock': 'stock',
    }

    def get_queryset(self):
        """Búsqueda y filtros por parámetros de la URL, ej.:
        /api/productos/?q=pulsera&categoria=2&precio_min=50000&precio_max=200000
                       &tipo_oro=amarillo&talla=18&orden=precio_asc
        """
        qs = Producto.objects.select_related('categoria')
        p = self.request.query_params

        if not es_admin(self.request.user):
            # El cliente solo ve productos activos de categorías activas
            qs = qs.filter(activo=True).filter(Q(categoria__isnull=True) | Q(categoria__activa=True))
        elif p.get('activo') in ('true', 'false'):
            qs = qs.filter(activo=p['activo'] == 'true')

        if p.get('categoria'):
            if not str(p['categoria']).isdigit():
                raise ErrorDeNegocio('La categoría seleccionada no es válida.')
            qs = qs.filter(categoria_id=p['categoria'])

        q = (p.get('q') or '').strip()                       # HU-VE-013 búsqueda por nombre
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

        precio_min = _decimal(p['precio_min'], 'precio mínimo') if p.get('precio_min') else None
        precio_max = _decimal(p['precio_max'], 'precio máximo') if p.get('precio_max') else None
        if precio_min is not None and precio_max is not None and precio_min > precio_max:
            raise ErrorDeNegocio('El precio mínimo no puede ser mayor que el máximo.')  # HU-VE-014
        if precio_min is not None:
            qs = qs.filter(precio__gte=precio_min)
        if precio_max is not None:
            qs = qs.filter(precio__lte=precio_max)

        tipo_oro = p.get('tipo_oro')                         # HU-VE-015
        if tipo_oro:
            if tipo_oro not in dict(Producto.TIPOS_ORO):
                raise ErrorDeNegocio('El tipo de oro seleccionado no es válido.')
            qs = qs.filter(tipo_oro=tipo_oro)

        if p.get('talla'):                                   # HU-IN-049
            qs = qs.filter(talla_cm=_decimal(p['talla'], 'talla'))

        if p.get('disponibles') == 'true':
            qs = qs.filter(stock__gt=0)

        return qs.order_by(self.ORDENES.get(p.get('orden'), '-creado'), 'id')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductoWriteSerializer
        return ProductoListSerializer

    def _respuesta(self, producto, codigo=status.HTTP_200_OK):
        return Response(ProductoListSerializer(producto, context={'request': self.request}).data, status=codigo)

    def create(self, request, *args, **kwargs):
        serializer = ProductoWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        producto = serializer.save()
        datos = ProductoListSerializer(producto, context={'request': request}).data
        datos['detail'] = 'Producto registrado correctamente.'
        return Response(datos, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = ProductoWriteSerializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return self._respuesta(serializer.save())

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        if producto.imagen:
            producto.imagen.storage.delete(producto.imagen.name)
        producto.delete()   # los pedidos antiguos conservan nombre y precio (FK SET NULL)
        return Response({'detail': 'Producto eliminado del catálogo.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def visibilidad(self, request, pk=None):
        """POST /api/productos/{id}/visibilidad/ -> muestra u oculta en la tienda"""
        producto = self.get_object()
        producto.activo = not producto.activo
        producto.save(update_fields=['activo', 'actualizado'])
        return self._respuesta(producto)

    @action(detail=False, methods=['get'], url_path='destacados')
    def destacados(self, request):
        """GET /api/productos/destacados/ -> los más vendidos visibles (para la portada)"""
        candidatos = list(
            self.get_queryset()
            .filter(stock__gt=0)
            .annotate(total_vendido=Sum('items_pedido__cantidad',
                                        filter=~Q(items_pedido__pedido__estado=Pedido.CANCELADO)))
            .order_by(F('total_vendido').desc(nulls_last=True), '-creado')
        )
        # Primero los más vendidos; para completar 4 tomamos una pieza por categoría,
        # así la portada no muestra una sola colección cuando aún no hay ventas.
        elegidos, categorias_usadas = [], set()
        for producto in candidatos:
            if producto.total_vendido or producto.categoria_id not in categorias_usadas:
                elegidos.append(producto)
                categorias_usadas.add(producto.categoria_id)
            if len(elegidos) == 4:
                break
        for producto in candidatos:          # si hay menos de 4 categorías, rellenamos
            if len(elegidos) == 4:
                break
            if producto not in elegidos:
                elegidos.append(producto)
        return Response(ProductoListSerializer(elegidos, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='opciones')
    def opciones(self, request):
        """GET /api/productos/opciones/ -> listas para los filtros y formularios"""
        return Response({
            'tipos_oro': [{'value': k, 'label': v} for k, v in Producto.TIPOS_ORO],
            'quilates': [{'value': k, 'label': v} for k, v in Producto.QUILATES],
            'elaboracion': [{'value': k, 'label': v} for k, v in Producto.ELABORACION],
            'tallas': ['16', '18', '20'],
            'metodos_pago': [{'value': k, 'label': v} for k, v in Pedido.METODOS_PAGO],
        })
