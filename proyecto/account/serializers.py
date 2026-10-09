import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Categoria, Producto, Carrito, ItemCarrito, Pedido, ItemPedido, Perfil

User = get_user_model()
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^[0-9+\-\s]{7,20}$')


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    telefono = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'rol', 'telefono',
        )

    def get_rol(self, obj):
        perfil = getattr(obj, 'perfil', None)
        if perfil:
            return perfil.rol
        return 'admin' if obj.is_staff else 'cliente'

    def get_telefono(self, obj):
        perfil = getattr(obj, 'perfil', None)
        return perfil.telefono if perfil else ''


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=4, max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    primer_nombre = serializers.CharField(max_length=40)
    apellidos = serializers.CharField(max_length=80)
    telefono = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_username(self, value):
        value = value.strip()
        if not re.match(r'^[a-zA-Z0-9._]+$', value):
            raise serializers.ValidationError(
                'El usuario solo puede tener letras, números, punto o guion bajo.'
            )
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Ese usuario ya está registrado.')
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if not EMAIL_RE.match(value):
            raise serializers.ValidationError('El correo no es válido.')
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ese correo ya está registrado.')
        return value

    def validate_primer_nombre(self, value):
        value = value.strip().title()
        if len(value) < 2:
            raise serializers.ValidationError('Escribe tu nombre.')
        return value

    def validate_apellidos(self, value):
        value = value.strip().title()
        if len(value) < 2:
            raise serializers.ValidationError('Escribe tus apellidos.')
        return value

    def validate_telefono(self, value):
        value = value.strip()
        if value and not PHONE_RE.match(value):
            raise serializers.ValidationError('El teléfono no es válido.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        telefono = validated_data.pop('telefono', '')
        validated_data.pop('password2')
        primer = validated_data.pop('primer_nombre')
        apellidos = validated_data.pop('apellidos')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=primer,
            last_name=apellidos,
        )
        perfil, _ = Perfil.objects.get_or_create(usuario=user)
        perfil.rol = Perfil.ROL_CLIENTE
        perfil.telefono = telefono
        perfil.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username', '').strip()
        password = attrs.get('password', '')
        if not username or not password:
            raise serializers.ValidationError('Usuario y contraseña son obligatorios.')
        attrs['username'] = username
        return attrs


class ActualizarPerfilSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=40)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
    telefono = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_email(self, value):
        user = self.context['request'].user
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Ese correo ya está en uso.')
        return value

    def validate_telefono(self, value):
        value = value.strip()
        if value and not PHONE_RE.match(value):
            raise serializers.ValidationError('El teléfono no es válido.')
        return value


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
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('El nombre de la categoría es muy corto.')
        qs = Categoria.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ya existe una categoría con ese nombre.')
        return value


class ProductoListSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = (
            'id', 'nombre', 'slug', 'descripcion', 'precio', 'stock',
            'imagen', 'imagen_url', 'activo', 'categoria', 'categoria_nombre',
        )

    def get_imagen_url(self, obj):
        if not obj.imagen:
            return None
        request = self.context.get('request')
        url = obj.imagen.url
        if request:
            return request.build_absolute_uri(url)
        return url


class ProductoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = (
            'id', 'nombre', 'descripcion', 'precio', 'stock',
            'imagen', 'activo', 'categoria',
        )

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
            if data.get('categoria') in ('', 'null', None):
                data['categoria'] = None
            activo = data.get('activo')
            if str(activo).lower() in ('false', '0', 'off'):
                data['activo'] = False
            elif str(activo).lower() in ('true', '1', 'on'):
                data['activo'] = True
        return super().to_internal_value(data)

    def validate_nombre(self, value):
        value = value.strip()
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

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('El stock no puede ser negativo.')
        return value


class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoListSerializer(read_only=True)
    producto_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarrito
        fields = ('id', 'producto', 'producto_id', 'cantidad', 'subtotal')

    def get_subtotal(self, obj):
        return obj.producto.precio * obj.cantidad

    def validate_cantidad(self, value):
        if value < 1:
            raise serializers.ValidationError('La cantidad mínima es 1.')
        return value

    def validate_producto_id(self, value):
        producto = Producto.objects.filter(pk=value, activo=True).first()
        if not producto:
            raise serializers.ValidationError('El producto no está disponible.')
        return value


class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    cantidad_items = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = ('id', 'items', 'total', 'cantidad_items', 'actualizado')

    def get_total(self, obj):
        return sum(i.producto.precio * i.cantidad for i in obj.items.all())

    def get_cantidad_items(self, obj):
        return sum(i.cantidad for i in obj.items.all())


class ItemPedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = ('id', 'producto', 'nombre', 'precio', 'cantidad', 'subtotal')

    def get_subtotal(self, obj):
        return obj.precio * obj.cantidad


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)

    class Meta:
        model = Pedido
        fields = (
            'id', 'usuario', 'usuario_username', 'usuario_email',
            'total', 'estado', 'notas', 'items', 'creado', 'actualizado',
        )
        read_only_fields = ('id', 'usuario', 'total', 'creado', 'actualizado')
