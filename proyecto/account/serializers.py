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
from rest_framework import serializers

from .models import Carrito, Categoria, ItemCarrito, ItemPedido, Pedido, Perfil, Producto
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
class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    telefono = serializers.CharField(source='perfil.telefono', default='', read_only=True)
    direccion = serializers.CharField(source='perfil.direccion', default='', read_only=True)
    ciudad = serializers.CharField(source='perfil.ciudad', default='', read_only=True)
    departamento = serializers.CharField(source='perfil.departamento', default='', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'rol',
            'telefono', 'direccion', 'ciudad', 'departamento', 'date_joined', 'last_login',
        )

    def get_rol(self, obj):
        return Perfil.ROL_ADMIN if es_admin(obj) else Perfil.ROL_CLIENTE


class ClienteAdminSerializer(UsuarioSerializer):
    """Lo que ve el administrador de cada cliente (HU-US-005)."""
    total_pedidos = serializers.IntegerField(read_only=True)
    total_comprado = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ('is_active', 'total_pedidos', 'total_comprado')


class RegistroSerializer(serializers.Serializer):
    """HU-US-001: registro de clientes."""
    username = serializers.CharField(min_length=4, max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    primer_nombre = serializers.CharField(max_length=40)
    apellidos = serializers.CharField(max_length=80)
    telefono = serializers.CharField(required=False, allow_blank=True, default='')

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

    def validate_telefono(self, value):
        return limpiar_telefono(value)

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
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['primer_nombre'],
            last_name=validated_data['apellidos'],
        )
        # La señal post_save ya creó el Perfil con rol 'cliente'
        Perfil.objects.filter(usuario=user).update(telefono=validated_data.get('telefono', ''))
        user.refresh_from_db()
        return user


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
    """HU-US-004: el cliente actualiza sus datos personales."""
    first_name = serializers.CharField(max_length=40)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
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

    def save(self, **kwargs):
        user = self.context['request'].user
        datos = self.validated_data
        user.first_name = datos['first_name']
        user.last_name = datos['last_name']
        user.email = datos['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])
        Perfil.objects.update_or_create(
            usuario=user,
            defaults={k: datos.get(k, '').strip() for k in ('telefono', 'direccion', 'ciudad', 'departamento')},
        )
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
            'orden', 'total_productos', 'creado', 'actualizado',
        )
        read_only_fields = ('id', 'slug', 'creado', 'actualizado', 'total_productos')

    def validate_nombre(self, value):
        value = ' '.join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError('El nombre de la categoría es muy corto.')
        qs = Categoria.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe una categoría con ese nombre.')
        return value


class ProductoListSerializer(serializers.ModelSerializer):
    """Formato de salida del producto (catálogo, detalle, panel admin)."""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True, default=None)
    imagen_url = serializers.SerializerMethodField()
    tipo_oro_display = serializers.CharField(source='get_tipo_oro_display', read_only=True)
    elaboracion_display = serializers.CharField(source='get_elaboracion_display', read_only=True)
    estado_stock = serializers.CharField(read_only=True)
    total_vendido = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Producto
        fields = (
            'id', 'nombre', 'slug', 'descripcion', 'precio', 'stock', 'stock_minimo',
            'estado_stock', 'imagen_url', 'activo', 'categoria', 'categoria_nombre',
            'tipo_oro', 'tipo_oro_display', 'quilates', 'peso_gramos', 'talla_cm',
            'elaboracion', 'elaboracion_display', 'creado', 'actualizado', 'total_vendido',
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

    class Meta:
        model = Producto
        fields = (
            'id', 'nombre', 'descripcion', 'precio', 'stock', 'stock_minimo', 'imagen',
            'quitar_imagen', 'activo', 'categoria', 'tipo_oro', 'quilates', 'peso_gramos',
            'talla_cm', 'elaboracion',
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
class CheckoutSerializer(serializers.Serializer):
    """Datos que pide el checkout: envío (HU-VE-019) y pago (HU-VE-020)."""
    nombre_destinatario = serializers.CharField(max_length=120)
    telefono_contacto = serializers.CharField(max_length=20)
    direccion_envio = serializers.CharField(max_length=200, min_length=6)
    ciudad = serializers.CharField(max_length=80)
    departamento = serializers.CharField(max_length=80)
    metodo_pago = serializers.ChoiceField(
        choices=Pedido.METODOS_PAGO,
        error_messages={'invalid_choice': 'Selecciona un método de pago válido.',
                        'required': 'Selecciona un método de pago.'},
    )
    notas = serializers.CharField(required=False, allow_blank=True, default='', max_length=500)
    guardar_direccion = serializers.BooleanField(required=False, default=True)

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
        fields = ('id', 'producto', 'nombre', 'precio', 'cantidad', 'subtotal')


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    estados_siguientes = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = (
            'id', 'usuario', 'usuario_username', 'usuario_email', 'usuario_nombre',
            'subtotal', 'descuento', 'total', 'estado', 'estado_display', 'estados_siguientes',
            'metodo_pago', 'metodo_pago_display', 'nombre_destinatario', 'telefono_contacto',
            'direccion_envio', 'ciudad', 'departamento', 'transportadora', 'numero_guia',
            'notas', 'items', 'creado', 'actualizado',
        )
        read_only_fields = fields

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username

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
        if attrs.get('estado') == Pedido.ENVIADO:
            guia = attrs.get('numero_guia', self.instance.numero_guia if self.instance else '')
            if not (guia or '').strip():
                raise serializers.ValidationError(
                    {'numero_guia': 'Para marcar como enviado registra el número de guía.'}
                )
        return attrs
