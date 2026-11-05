"""
Serializers = traductores entre objetos de Python y JSON.

  - Hacia afuera (respuesta): convierten un Producto en {"id": 1, "nombre": ...}
  - Hacia adentro (petición): VALIDAN los datos que envía el frontend antes de
    guardarlos. Si algo está mal, DRF responde 400 con el mensaje de error.
    (HU-SE-033 y HU-SE-034: validar formatos y campos obligatorios)
"""
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from . import referencias
from .models import Carrito, Categoria, Cliente, ItemCarrito, ItemPedido, Pedido, Perfil, Producto
from .permissions import es_admin
from .services import calcular_totales

User = get_user_model()
USERNAME_RE = re.compile(r'^[a-zA-Z0-9._]+$')
PHONE_RE = re.compile(r'^[0-9+\-\s()]{7,20}$')
NOMBRE_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")


def limpiar_nombre(valor, campo):
    valor = ' '.join(valor.split()).title()
    if len(valor) < 2:
        raise serializers.ValidationError(f'Escribe {campo}.')
    if not NOMBRE_RE.match(valor):
        raise serializers.ValidationError(f'{campo.capitalize()} solo puede tener letras.')
    return valor


def limpiar_telefono(valor):
    valor = (valor or '').strip()
    if valor and not PHONE_RE.match(valor):
        raise serializers.ValidationError('El teléfono no es válido (7 a 20 dígitos).')
    return valor


# Formato permitido según el tipo de documento
FORMATOS_DOCUMENTO = {
    'CC': (re.compile(r'^\d{6,10}$'), 'La cédula debe tener entre 6 y 10 números.'),
    'TI': (re.compile(r'^\d{6,11}$'), 'La tarjeta de identidad debe tener entre 6 y 11 números.'),
    'CE': (re.compile(r'^[A-Za-z0-9]{4,12}$'), 'La cédula de extranjería debe tener entre 4 y 12 letras o números.'),
    'PAS': (re.compile(r'^[A-Za-z0-9]{5,15}$'), 'El pasaporte debe tener entre 5 y 15 letras o números.'),
}


def limpiar_documento(tipo, numero):
    """Quita puntos y espacios ("1.234.567" -> "1234567") y valida el formato."""
    numero = re.sub(r'[\s.\-]', '', numero or '').upper()
    patron, mensaje = FORMATOS_DOCUMENTO[tipo]
    if not patron.match(numero):
        raise serializers.ValidationError({'numero_documento': mensaje})
    return numero


def url_publica_imagen(imagen, request=None):
    """Devuelve la URL completa de la imagen de un producto.

    - Producción: URL pública del bucket de Supabase.
    - Local: http://127.0.0.1:8000/media/productos/archivo.jpg
    """
    if not imagen:
        return None
    if settings.SUPABASE_URL:
        nombre = Path(imagen.name).name
        return (
            f'{settings.SUPABASE_URL}/storage/v1/object/public/'
            f'{settings.SUPABASE_BUCKET}/{nombre}'
        )
    url = imagen.url
    return request.build_absolute_uri(url) if request else url


# ===========================================================================
# USUARIOS Y AUTENTICACIÓN
# ===========================================================================
def cliente_de(user):
    """El Cliente asociado a una cuenta, o None (por ejemplo, un administrador)."""
    try:
        return user.cliente
    except Cliente.DoesNotExist:
        return None


class UsuarioSerializer(serializers.ModelSerializer):
    """La CUENTA (usuario) y, si ya compró, los datos de su CLIENTE.

    Un usuario solo es cliente cuando hace su primera compra (o si ya había
    comprado en el local). Mientras tanto es_cliente = False.
    """
    rol = serializers.SerializerMethodField()
    cliente_id = serializers.SerializerMethodField()
    es_cliente = serializers.SerializerMethodField()
    telefono = serializers.SerializerMethodField()
    direccion = serializers.SerializerMethodField()
    ciudad = serializers.SerializerMethodField()
    departamento = serializers.SerializerMethodField()
    tipo_documento = serializers.SerializerMethodField()
    numero_documento = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'rol', 'cliente_id', 'es_cliente',
            'tipo_documento', 'numero_documento', 'telefono', 'direccion', 'ciudad', 'departamento',
            'date_joined', 'last_login',
        )

    def get_rol(self, obj):
        return Perfil.ROL_ADMIN if es_admin(obj) else Perfil.ROL_CLIENTE

    def get_cliente_id(self, obj):
        cliente = cliente_de(obj)
        return cliente.id if cliente else None

    def get_es_cliente(self, obj):
        return cliente_de(obj) is not None

    def _dato(self, obj, campo):
        cliente = cliente_de(obj)
        return getattr(cliente, campo) if cliente else ''

    def get_telefono(self, obj):
        return self._dato(obj, 'telefono')

    def get_direccion(self, obj):
        return self._dato(obj, 'direccion')

    def get_ciudad(self, obj):
        return self._dato(obj, 'ciudad')

    def get_departamento(self, obj):
        return self._dato(obj, 'departamento')

    def get_tipo_documento(self, obj):
        return self._dato(obj, 'tipo_documento') or 'CC'

    def get_numero_documento(self, obj):
        return self._dato(obj, 'numero_documento')


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Las CUENTAS, como las ve el administrador: todos son usuarios; algunos ya son clientes."""
    rol = serializers.SerializerMethodField()
    es_cliente = serializers.SerializerMethodField()
    cliente_id = serializers.IntegerField(source='cliente.id', read_only=True, default=None)
    total_pedidos = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'rol', 'is_active',
                  'es_cliente', 'cliente_id', 'total_pedidos', 'date_joined', 'last_login')

    def get_rol(self, obj):
        return Perfil.ROL_ADMIN if es_admin(obj) else Perfil.ROL_CLIENTE

    def get_es_cliente(self, obj):
        return cliente_de(obj) is not None


class ClienteSerializer(serializers.ModelSerializer):
    """El CLIENTE, como lo ve y edita el administrador (HU-US-005).

    Sirve también para registrar clientes que compran en el local, sin cuenta.
    """
    tiene_cuenta = serializers.SerializerMethodField()
    usuario_username = serializers.CharField(source='usuario.username', read_only=True, default=None)
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)
    total_pedidos = serializers.IntegerField(read_only=True, default=0)
    total_comprado = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    numero_documento = serializers.CharField(max_length=20, error_messages={
        'required': 'Escribe el número de documento.', 'blank': 'Escribe el número de documento.'})

    class Meta:
        model = Cliente
        fields = (
            'id', 'tipo_documento', 'tipo_documento_display', 'numero_documento', 'nombres', 'apellidos',
            'correo', 'telefono', 'direccion', 'ciudad', 'departamento', 'tiene_cuenta', 'usuario_username',
            'total_pedidos', 'total_comprado', 'eliminado_en', 'creado',
        )
        read_only_fields = ('id', 'eliminado_en', 'creado')

    def get_tiene_cuenta(self, obj):
        return obj.usuario_id is not None

    def validate_nombres(self, value):
        return limpiar_nombre(value, 'los nombres')

    def validate_apellidos(self, value):
        return limpiar_nombre(value, 'los apellidos') if value.strip() else ''

    def validate_telefono(self, value):
        return limpiar_telefono(value)

    def validate(self, attrs):
        tipo = attrs.get('tipo_documento', getattr(self.instance, 'tipo_documento', 'CC'))
        if 'numero_documento' in attrs or 'tipo_documento' in attrs:
            numero = limpiar_documento(tipo, attrs.get('numero_documento', getattr(self.instance, 'numero_documento', '')))
            otros = Cliente.todos.filter(tipo_documento=tipo, numero_documento=numero)
            if self.instance:
                otros = otros.exclude(pk=self.instance.pk)
            if otros.exists():
                raise serializers.ValidationError({'numero_documento': 'Ya existe un cliente con ese documento.'})
            attrs['numero_documento'] = numero
        return attrs


class RegistroSerializer(serializers.Serializer):
    """HU-US-001: registro de USUARIOS (la cuenta para entrar a la tienda).

    Registrarse NO crea un cliente: la persona se vuelve cliente cuando compra
    (ver services.cliente_para_compra).
    """
    username = serializers.CharField(min_length=4, max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    primer_nombre = serializers.CharField(max_length=40)
    apellidos = serializers.CharField(max_length=80)

    def validate_username(self, value):
        value = value.strip()
        if not USERNAME_RE.match(value):
            raise serializers.ValidationError('El usuario solo puede tener letras, números, punto o guion bajo.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Ese usuario ya está registrado.')
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ese correo ya está registrado.')
        return value

    def validate_primer_nombre(self, value):
        return limpiar_nombre(value, 'tu nombre')

    def validate_apellidos(self, value):
        return limpiar_nombre(value, 'tus apellidos')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        usuario_temporal = User(
            username=attrs['username'], email=attrs['email'],
            first_name=attrs['primer_nombre'], last_name=attrs['apellidos'],
        )
        try:
            validate_password(attrs['password'], user=usuario_temporal)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        """Crea el usuario; la señal post_save le crea su Perfil con rol 'cliente'."""
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['primer_nombre'],
            last_name=validated_data['apellidos'],
        )


class LoginSerializer(serializers.Serializer):
    """HU-AU-002: se puede entrar con el usuario O con el correo."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=128)

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Escribe tu usuario o correo.')
        return value


class ActualizarPerfilSerializer(serializers.Serializer):
    """HU-US-004: el usuario actualiza sus datos.

    Nombre y correo son de la CUENTA. Documento, teléfono y dirección son del
    CLIENTE, así que solo se guardan si la persona ya compró alguna vez.
    """
    first_name = serializers.CharField(max_length=40)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
    tipo_documento = serializers.ChoiceField(choices=Cliente.TIPOS_DOCUMENTO, required=False)
    numero_documento = serializers.CharField(required=False, allow_blank=True, max_length=20)
    telefono = serializers.CharField(required=False, allow_blank=True, default='')
    direccion = serializers.CharField(required=False, allow_blank=True, default='', max_length=200)
    ciudad = serializers.CharField(required=False, allow_blank=True, default='', max_length=80)
    departamento = serializers.CharField(required=False, allow_blank=True, default='', max_length=80)

    def validate_first_name(self, value):
        return limpiar_nombre(value, 'tu nombre')

    def validate_last_name(self, value):
        return limpiar_nombre(value, 'tus apellidos')

    def validate_email(self, value):
        user = self.context['request'].user
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Ese correo ya está en uso.')
        return value

    def validate_telefono(self, value):
        return limpiar_telefono(value)

    def validate(self, attrs):
        numero = (attrs.get('numero_documento') or '').strip()
        propio = cliente_de(self.context['request'].user)
        if numero and propio:
            tipo = attrs.get('tipo_documento', 'CC')
            numero = limpiar_documento(tipo, numero)
            otros = Cliente.todos.filter(tipo_documento=tipo, numero_documento=numero).exclude(pk=propio.pk)
            if otros.exists():
                raise serializers.ValidationError({'numero_documento': 'Ese documento ya está registrado.'})
            attrs['numero_documento'] = numero
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        user = self.context['request'].user
        datos = self.validated_data
        user.first_name = datos['first_name']
        user.last_name = datos['last_name']
        user.email = datos['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])
        cliente = cliente_de(user)
        if cliente is None:          # aún no ha comprado: solo es usuario
            user.refresh_from_db()
            return user
        cliente.nombres = datos['first_name']
        cliente.apellidos = datos['last_name']
        cliente.correo = datos['email']
        for campo in ('telefono', 'direccion', 'ciudad', 'departamento'):
            setattr(cliente, campo, datos.get(campo, '').strip())
        if datos.get('numero_documento'):
            cliente.tipo_documento = datos.get('tipo_documento', cliente.tipo_documento)
            cliente.numero_documento = datos['numero_documento']
        cliente.save()
        user.refresh_from_db()
        return user


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['password_actual']):
            raise serializers.ValidationError({'password_actual': 'La contraseña actual no es correcta.'})
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs


class SolicitarRecuperacionSerializer(serializers.Serializer):
    """HU-US-003 paso 1: el usuario escribe su correo."""
    email = serializers.EmailField()


class ConfirmarRecuperacionSerializer(serializers.Serializer):
    """HU-US-003 paso 2: con el enlace recibido define la nueva contraseña."""
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return attrs


# ===========================================================================
# CATÁLOGO
# ===========================================================================
class CategoriaSerializer(serializers.ModelSerializer):
    total_productos = serializers.IntegerField(read_only=True)

    class Meta:
        model = Categoria
        fields = (
            'id', 'nombre', 'slug', 'descripcion', 'activa',
            'orden', 'total_productos', 'eliminado_en', 'creado', 'actualizado',
        )
        read_only_fields = ('id', 'slug', 'eliminado_en', 'creado', 'actualizado', 'total_productos')

    def validate_nombre(self, value):
        value = ' '.join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError('El nombre de la categoría es muy corto.')
        qs = Categoria.todos.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        existente = qs.first()
        if existente and existente.eliminado_en:
            raise serializers.ValidationError('Hay una categoría con ese nombre en la Papelera: restáurala.')
        if existente:
            raise serializers.ValidationError('Ya existe una categoría con ese nombre.')
        return value


class ProductoListSerializer(serializers.ModelSerializer):
    """Formato de salida del producto (catálogo, detalle, panel admin)."""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)
    imagen_url = serializers.SerializerMethodField()
    tipo_oro_display = serializers.CharField(source='get_tipo_oro_display', read_only=True)
    elaboracion_display = serializers.CharField(source='get_elaboracion_display', read_only=True)
    tipo_pieza_display = serializers.CharField(source='get_tipo_pieza_display', read_only=True)
    piedra_display = serializers.CharField(source='get_piedra_display', read_only=True)
    estado_stock = serializers.CharField(read_only=True)
    total_vendido = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Producto
        fields = (
            'id', 'referencia', 'nombre', 'slug', 'descripcion', 'precio', 'stock', 'stock_minimo',
            'estado_stock', 'imagen_url', 'activo', 'categoria', 'categoria_nombre',
            'tipo_pieza', 'tipo_pieza_display', 'piedra', 'piedra_display',
            'tipo_oro', 'tipo_oro_display', 'quilates', 'peso_gramos', 'talla_cm',
            'elaboracion', 'elaboracion_display', 'eliminado_en', 'creado', 'actualizado', 'total_vendido',
        )

    def get_imagen_url(self, obj):
        return url_publica_imagen(obj.imagen, self.context.get('request'))


class ProductoWriteSerializer(serializers.ModelSerializer):
    """Validación al crear/editar un producto desde el panel admin
    (HU-IN-006, HU-IN-007, HU-IN-009, HU-IN-010)."""
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(),
        error_messages={
            'required': 'Selecciona una categoría.',
            'null': 'Selecciona una categoría.',
            'does_not_exist': 'La categoría seleccionada no es válida.',
            'incorrect_type': 'La categoría seleccionada no es válida.',
        },
    )
    quitar_imagen = serializers.BooleanField(write_only=True, required=False, default=False)
    # Vacía = el sistema la genera (TIPO-QUILATES-COLOR-PIEDRA-NNN). Al editar, vacía = no cambia.
    referencia = serializers.CharField(required=False, allow_blank=True, max_length=60)

    class Meta:
        model = Producto
        fields = (
            'id', 'referencia', 'nombre', 'descripcion', 'precio', 'stock', 'stock_minimo', 'imagen',
            'quitar_imagen', 'activo', 'categoria', 'tipo_pieza', 'piedra', 'tipo_oro', 'quilates',
            'peso_gramos', 'talla_cm', 'elaboracion',
        )
        extra_kwargs = {
            'precio': {'error_messages': {'invalid': 'El precio debe ser un número.'}},
            'stock': {'error_messages': {'invalid': 'El stock debe ser un número entero.'}},
        }

    def to_internal_value(self, data):
        # Los formularios con imagen llegan como multipart (todo es texto).
        # Convertimos '' en None para los campos opcionales numéricos.
        if hasattr(data, 'copy'):
            data = data.copy()
            for campo in ('quilates', 'peso_gramos', 'talla_cm'):
                if campo in data and data.get(campo) in ('', 'null', 'undefined'):
                    data[campo] = None
            if data.get('categoria') in ('null', 'undefined'):
                data['categoria'] = ''
        return super().to_internal_value(data)

    def validate_nombre(self, value):
        value = ' '.join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError('El nombre del producto es muy corto.')
        return value

    def validate_referencia(self, value):
        value = referencias.normalizar(value)
        if not value:
            return ''
        if not referencias.es_valida(value):
            raise serializers.ValidationError(
                'Usa de 3 a 40 letras, números y guiones. Ej.: AN-18K-BL-DI-001.')
        otro = Producto.todos.filter(referencia=value)
        if self.instance is not None:
            otro = otro.exclude(pk=self.instance.pk)
        otro = otro.first()
        if otro:
            donde = ' (está en la Papelera)' if otro.eliminado_en else ''
            raise serializers.ValidationError(f'Esa referencia ya es de "{otro.nombre}"{donde}.')
        return value

    def validate_descripcion(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError('La descripción debe tener al menos 10 caracteres.')
        return value

    def validate_precio(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('El precio debe ser mayor a 0.')
        return value

    def validate_peso_gramos(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('El peso debe ser mayor a 0.')
        return value

    def validate_talla_cm(self, value):
        if value is not None and not (10 <= value <= 30):
            raise serializers.ValidationError('La talla debe estar entre 10 y 30 cm.')
        return value

    def validate_imagen(self, imagen):
        """HU-IN-009: solo formatos permitidos y tamaño máximo."""
        if not imagen:
            return imagen
        extension = Path(imagen.name).suffix.lower().lstrip('.')
        if extension not in settings.IMAGEN_FORMATOS:
            raise serializers.ValidationError(
                f'Formato no permitido. Usa: {", ".join(settings.IMAGEN_FORMATOS)}.'
            )
        if imagen.size > settings.IMAGEN_MAX_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f'La imagen supera el tamaño máximo de {settings.IMAGEN_MAX_MB} MB.'
            )
        return imagen

    def validate(self, attrs):
        if self.instance is None and not attrs.get('categoria'):
            raise serializers.ValidationError({'categoria': 'Selecciona una categoría.'})
        return attrs

    def _guardar(self, instancia, datos):
        quitar = datos.pop('quitar_imagen', False)
        imagen_nueva = datos.pop('imagen', None)
        if not datos.get('referencia'):
            datos.pop('referencia', None)       # vacía: se genera (nuevo) o se conserva (edición)
        imagen_vieja = instancia.imagen.name if instancia.imagen else None
        for campo, valor in datos.items():
            setattr(instancia, campo, valor)
        if imagen_nueva:
            instancia.imagen = imagen_nueva
        elif quitar:
            instancia.imagen = None
        instancia.save()
        # Borramos la imagen anterior del almacenamiento para no dejar basura
        if imagen_vieja and (imagen_nueva or quitar):
            instancia.imagen.storage.delete(imagen_vieja)
        return instancia

    def create(self, validated_data):
        return self._guardar(Producto(), validated_data)

    def update(self, instance, validated_data):
        return self._guardar(instance, validated_data)


# ===========================================================================
# CARRITO
# ===========================================================================
class AgregarAlCarritoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField(min_value=1)
    cantidad = serializers.IntegerField(min_value=1, max_value=99, default=1)


class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoListSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ('id', 'producto', 'cantidad', 'subtotal')


class CarritoSerializer(serializers.ModelSerializer):
    """HU-CO-018: el carrito muestra subtotal, descuento por volumen y total."""
    items = serializers.SerializerMethodField()
    resumen = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = ('id', 'items', 'resumen', 'actualizado')

    def _items(self, obj):
        if not hasattr(self, '_cache_items'):
            self._cache_items = list(
                obj.items.select_related('producto__categoria').order_by('agregado')
            )
        return self._cache_items

    def get_items(self, obj):
        return ItemCarritoSerializer(self._items(obj), many=True, context=self.context).data

    def get_resumen(self, obj):
        totales = calcular_totales([(i.producto.precio, i.cantidad) for i in self._items(obj)])
        return {
            'cantidad_items': totales['piezas'],
            'subtotal': totales['subtotal'],
            'porcentaje_descuento': totales['porcentaje_descuento'],
            'descuento': totales['descuento'],
            'total': totales['total'],
        }


# ===========================================================================
# PEDIDOS
# ===========================================================================
class LineaVentaSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1, max_value=999)


class VentaLocalSerializer(serializers.Serializer):
    """Venta en el local: un cliente (existente o nuevo) + lo que compró."""
    cliente_id = serializers.IntegerField(required=False)
    cliente = serializers.DictField(required=False)      # datos de un cliente nuevo (ClienteSerializer)
    items = LineaVentaSerializer(many=True, allow_empty=False, error_messages={
        'empty': 'Agrega al menos un producto.', 'not_a_list': 'Agrega al menos un producto.'})
    metodo_pago = serializers.ChoiceField(choices=Pedido.METODOS_PAGO, error_messages={
        'invalid_choice': 'Selecciona un método de pago.', 'required': 'Selecciona un método de pago.'})
    notas = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)

    def validate(self, attrs):
        if not attrs.get('cliente_id') and not attrs.get('cliente'):
            raise serializers.ValidationError({'cliente': 'Indica quién hizo la compra.'})
        return attrs


class CheckoutSerializer(serializers.Serializer):
    """Datos que pide el checkout: envío (HU-VE-019) y pago (HU-VE-020)."""
    nombre_destinatario = serializers.CharField(max_length=120)
    telefono_contacto = serializers.CharField(max_length=20)
    direccion_envio = serializers.CharField(max_length=200, min_length=6)
    ciudad = serializers.CharField(max_length=80)
    departamento = serializers.CharField(max_length=80)
    metodo_pago = serializers.ChoiceField(
        choices=[m for m in Pedido.METODOS_PAGO if m[0] != 'efectivo'],   # efectivo solo en el local
        error_messages={'invalid_choice': 'Selecciona un método de pago válido.',
                        'required': 'Selecciona un método de pago.'},
    )
    notas = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)
    guardar_direccion = serializers.BooleanField(required=False, default=True)
    # Solo se piden si el cliente todavía no tiene documento (clientes antiguos)
    tipo_documento = serializers.ChoiceField(choices=Cliente.TIPOS_DOCUMENTO, required=False)
    numero_documento = serializers.CharField(required=False, allow_blank=True, max_length=20)

    def validate_nombre_destinatario(self, value):
        return limpiar_nombre(value, 'el nombre de quien recibe')

    def validate_telefono_contacto(self, value):
        value = limpiar_telefono(value)
        if not value:
            raise serializers.ValidationError('Escribe un teléfono de contacto.')
        return value


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ('id', 'producto', 'referencia', 'nombre', 'precio', 'cantidad', 'subtotal')


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    cliente_documento = serializers.SerializerMethodField()
    cliente_correo = serializers.CharField(source='cliente.correo', read_only=True)
    cliente_usuario = serializers.CharField(source='cliente.usuario.username', read_only=True, default=None)
    registrado_por_username = serializers.CharField(source='registrado_por.username', read_only=True, default=None)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    estados_siguientes = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = (
            'id', 'cliente', 'cliente_nombre', 'cliente_documento', 'cliente_correo', 'cliente_usuario',
            'registrado_por_username',
            'subtotal', 'descuento', 'total', 'estado', 'estado_display', 'estados_siguientes',
            'metodo_pago', 'metodo_pago_display', 'nombre_destinatario', 'telefono_contacto',
            'direccion_envio', 'ciudad', 'departamento', 'transportadora', 'numero_guia',
            'notas', 'items', 'creado', 'actualizado',
        )
        read_only_fields = fields

    def get_cliente_documento(self, obj):
        c = obj.cliente
        return f'{c.tipo_documento} {c.numero_documento}' if c.numero_documento else ''

    def get_estados_siguientes(self, obj):
        return sorted(Pedido.TRANSICIONES.get(obj.estado, set()))


class PedidoAdminUpdateSerializer(serializers.Serializer):
    """HU-PE-024 y HU-PE-050: el admin cambia el estado y registra la guía."""
    estado = serializers.ChoiceField(choices=Pedido.ESTADOS, required=False)
    transportadora = serializers.CharField(max_length=60, required=False, allow_blank=True)
    numero_guia = serializers.CharField(max_length=60, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('No enviaste ningún cambio.')
        puede_enviar = self.instance is None or self.instance.puede_cambiar_a(Pedido.ENVIADO)
        if attrs.get('estado') == Pedido.ENVIADO and puede_enviar:
            guia = attrs.get('numero_guia', self.instance.numero_guia if self.instance else '')
            if not (guia or '').strip():
                raise serializers.ValidationError(
                    {'numero_guia': 'Para marcar como enviado registra el número de guía.'}
                )
        return attrs
