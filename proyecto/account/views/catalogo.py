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

from django.db.models import Case, Count, F, IntegerField, Q, Sum, When
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .. import referencias, services
from ..exceptions import ErrorDeNegocio
from ..models import Categoria, Pedido, Producto
from ..permissions import LecturaPublicaEscrituraAdmin, es_admin
from ..serializers import CategoriaSerializer, ProductoListSerializer, ProductoWriteSerializer


class CategoriaViewSet(viewsets.ModelViewSet):
    serializer_class = CategoriaSerializer
    permission_classes = [LecturaPublicaEscrituraAdmin]

    def get_queryset(self):
        qs = Categoria.objects.order_by('nombre')
        vigentes = Q(productos__eliminado_en__isnull=True)    # no contar lo que está en la papelera
        if es_admin(self.request.user):
            return qs.annotate(total_productos=Count('productos', filter=vigentes))
        # Clientes: solo categorías activas y conteo de productos visibles
        return qs.filter(activa=True).annotate(
            total_productos=Count('productos', filter=vigentes & Q(productos__activo=True))
        )

    def destroy(self, request, *args, **kwargs):
        # Borrado LÓGICO: va a la papelera. Sus productos se conservan, pero no se
        # ven en la tienda mientras la categoría esté en la papelera.
        categoria = self.get_object()
        services.mover_a_papelera(categoria)
        return Response({'detail': f'"{categoria.nombre}" se movió a la Papelera.'})


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
            qs = qs.filter(activo=True).filter(
                Q(categoria__isnull=True) | Q(categoria__activa=True, categoria__eliminado_en__isnull=True)
            )
        elif p.get('activo') in ('true', 'false'):
            qs = qs.filter(activo=p['activo'] == 'true')

        if p.get('categoria'):
            if not str(p['categoria']).isdigit():
                raise ErrorDeNegocio('La categoría seleccionada no es válida.')
            qs = qs.filter(categoria_id=p['categoria'])

        q = (p.get('q') or '').strip()                       # HU-VE-013 búsqueda por nombre o referencia
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q)
                           | Q(referencia__startswith=referencias.normalizar(q)))

        if p.get('referencia'):                              # exacta: la que lee el lector de códigos
            qs = qs.filter(referencia=referencias.normalizar(p['referencia']))

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

    def list(self, request, *args, **kwargs):
        """Con ?limite=N devuelve solo los N primeros (buscador rápido del panel).

        Si se busca con ?q=, primero salen los productos cuya referencia empieza
        por lo escrito, después los que coinciden por nombre.
        """
        qs = self.get_queryset()
        limite = request.query_params.get('limite')
        if limite:
            if not limite.isdigit():
                raise ErrorDeNegocio('El límite debe ser un número.')
            q = referencias.normalizar(request.query_params.get('q'))
            if q:
                qs = qs.annotate(prioridad=Case(When(referencia__startswith=q, then=0), default=1,
                                                output_field=IntegerField())).order_by('prioridad', 'referencia')
            qs = qs[:min(max(int(limite), 1), 50)]
        return Response(ProductoListSerializer(qs, many=True, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='sugerir-referencia')
    def sugerir_referencia(self, request):
        """GET /api/productos/sugerir-referencia/?tipo_pieza=anillo&quilates=18&tipo_oro=blanco&piedra=diamante
        -> {"referencia": "AN-18K-BL-DI-003"}  (solo admin)"""
        if not es_admin(request.user):
            raise ErrorDeNegocio('Solo el administrador puede realizar esta acción.', 403)
        p = request.query_params
        quilates = p.get('quilates') or None
        if quilates and (not quilates.isdigit() or int(quilates) not in dict(Producto.QUILATES)):
            raise ErrorDeNegocio('Los quilates no son válidos.')
        borrador = Producto(tipo_pieza=p.get('tipo_pieza') or 'otro', quilates=quilates,
                            tipo_oro=p.get('tipo_oro') or '', piedra=p.get('piedra') or '')
        return Response({'referencia': borrador.generar_referencia()})

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
        # Borrado LÓGICO: va a la papelera, desde donde se puede restaurar o
        # eliminar definitivamente (ver views/admin.py -> papelera).
        producto = self.get_object()
        services.mover_a_papelera(producto)
        return Response({'detail': f'"{producto.nombre}" se movió a la Papelera.'}, status=status.HTTP_200_OK)

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
            'tipos_pieza': [{'value': v, 'label': t, 'codigo': c} for v, t, c in referencias.TIPOS_PIEZA],
            'piedras': [{'value': v, 'label': t, 'codigo': c} for v, t, c in referencias.PIEDRAS],
            'tallas': ['16', '18', '20'],
            'metodos_pago': [{'value': k, 'label': v} for k, v in Pedido.METODOS_PAGO],
        })
