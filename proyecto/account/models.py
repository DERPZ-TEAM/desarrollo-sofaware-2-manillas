"""
Modelos = tablas de la base de datos.

Cada clase se convierte en una tabla de PostgreSQL y cada atributo en una
columna. Django crea/actualiza las tablas con "python manage.py migrate".

Relaciones (llaves foráneas = FK):
    auth_user 1───1 account_perfil        (rol cliente/admin, teléfono)
    auth_user 1───1 carrito 1───* item_carrito *───1 producto
    auth_user 1───* pedido 1───* item_pedido *───1 producto
    account_categoria 1───* producto
"""
import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


def generar_slug_unico(modelo, texto, instancia_pk=None, max_len=140):
    """Crea un 'slug' (texto para URL, ej. 'pulsera-oro-18k') que no se repita."""
    base = (slugify(texto) or 'item')[: max_len - 6]
    slug, n = base, 1
    while modelo.objects.filter(slug=slug).exclude(pk=instancia_pk).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug


def ruta_imagen_producto(instancia, nombre_archivo):
    """Nombre único para cada imagen subida: productos/<uuid>.<ext>.

    Así dos fotos llamadas 'foto.jpg' nunca se sobrescriben.
    """
    extension = Path(nombre_archivo).suffix.lower() or '.jpg'
    return f'productos/{uuid.uuid4().hex}{extension}'


class Perfil(models.Model):
    """Datos extra del usuario. Aquí vive el campo ROL (cliente / admin)."""
    ROL_CLIENTE = 'cliente'
    ROL_ADMIN = 'admin'
    ROLES = (
        (ROL_CLIENTE, 'Cliente'),
        (ROL_ADMIN, 'Administrador'),
    )

    id = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(          # FK única hacia auth_user
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_CLIENTE, db_index=True)
    telefono = models.CharField(max_length=20, blank=True, default='')
    # Datos de envío guardados para autocompletar el checkout (HU-VE-019)
    direccion = models.CharField(max_length=200, blank=True, default='')
    ciudad = models.CharField(max_length=80, blank=True, default='')
    departamento = models.CharField(max_length=80, blank=True, default='')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account_perfil'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f'{self.usuario.username} ({self.rol})'


class Categoria(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    descripcion = models.TextField(blank=True, default='')
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account_categoria'
        ordering = ['orden', 'nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generar_slug_unico(Categoria, self.nombre, self.pk, max_len=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Un brazalete / pieza de joyería del catálogo."""
    TIPOS_ORO = (
        ('amarillo', 'Oro amarillo'),
        ('blanco', 'Oro blanco'),
        ('rosa', 'Oro rosa'),
        ('laminado', 'Oro laminado'),
        ('golfi', 'Golfi / baño de oro'),
    )
    QUILATES = ((10, '10k'), (14, '14k'), (18, '18k'), (24, '24k'))
    ELABORACION = (('manual', 'Tejido a mano'), ('maquina', 'Hecho a máquina'))

    id = models.BigAutoField(primary_key=True)
    categoria = models.ForeignKey(           # FK hacia account_categoria
        Categoria,
        on_delete=models.SET_NULL,           # si borran la categoría, el producto queda sin categoría
        null=True,
        blank=True,
        related_name='productos',
        db_index=True,
    )
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=3)   # alerta de bajo stock (HU-IN-048)
    imagen = models.ImageField(upload_to=ruta_imagen_producto, blank=True, null=True)
    activo = models.BooleanField(default=True, db_index=True)
    # Ficha técnica (HU-PR-035, HU-VE-015, HU-IN-049, HU-PR-038)
    tipo_oro = models.CharField(max_length=20, choices=TIPOS_ORO, blank=True, default='', db_index=True)
    quilates = models.PositiveSmallIntegerField(choices=QUILATES, null=True, blank=True)
    peso_gramos = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    talla_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    elaboracion = models.CharField(max_length=10, choices=ELABORACION, blank=True, default='')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'producto'
        ordering = ['-creado']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['activo', 'categoria']),
            models.Index(fields=['precio']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generar_slug_unico(Producto, self.nombre, self.pk)
        super().save(*args, **kwargs)

    @property
    def estado_stock(self):
        """'agotado', 'bajo' u 'ok' según las existencias."""
        if self.stock == 0:
            return 'agotado'
        if self.stock <= self.stock_minimo:
            return 'bajo'
        return 'ok'

    def __str__(self):
        return self.nombre


class Carrito(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(          # cada cliente tiene UN carrito
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carrito'

    def __str__(self):
        return f'Carrito de {self.usuario.username}'


class ItemCarrito(models.Model):
    id = models.BigAutoField(primary_key=True)
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='items_carrito')
    cantidad = models.PositiveIntegerField(default=1)
    agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_carrito'
        constraints = [
            # Un mismo producto aparece una sola vez por carrito (se suma la cantidad)
            models.UniqueConstraint(fields=['carrito', 'producto'], name='uniq_item_carrito_producto'),
        ]

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'


class Pedido(models.Model):
    PENDIENTE = 'pendiente'
    CONFIRMADO = 'confirmado'
    ENVIADO = 'enviado'
    ENTREGADO = 'entregado'
    CANCELADO = 'cancelado'
    ESTADOS = (
        (PENDIENTE, 'Pendiente'),
        (CONFIRMADO, 'Confirmado'),
        (ENVIADO, 'Enviado'),
        (ENTREGADO, 'Entregado'),
        (CANCELADO, 'Cancelado'),
    )
    # Máquina de estados: desde cada estado, a cuáles se puede pasar.
    TRANSICIONES = {
        PENDIENTE: {CONFIRMADO, CANCELADO},
        CONFIRMADO: {ENVIADO, CANCELADO},
        ENVIADO: {ENTREGADO},
        ENTREGADO: set(),
        CANCELADO: set(),
    }

    METODOS_PAGO = (
        ('contraentrega', 'Pago contra entrega'),
        ('transferencia', 'Transferencia bancaria'),
        ('nequi', 'Nequi / Daviplata'),
        ('tarjeta', 'Tarjeta (simulado)'),
    )

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,             # no se puede borrar un usuario con pedidos
        related_name='pedidos',
    )
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE, db_index=True)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='contraentrega')
    # Datos de envío (HU-VE-019)
    nombre_destinatario = models.CharField(max_length=120, blank=True, default='')
    telefono_contacto = models.CharField(max_length=20, blank=True, default='')
    direccion_envio = models.CharField(max_length=200, blank=True, default='')
    ciudad = models.CharField(max_length=80, blank=True, default='')
    departamento = models.CharField(max_length=80, blank=True, default='')
    # Seguimiento del envío (HU-PE-050)
    transportadora = models.CharField(max_length=60, blank=True, default='')
    numero_guia = models.CharField(max_length=60, blank=True, default='')
    notas = models.TextField(blank=True, default='')
    creado = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pedido'
        ordering = ['-creado']
        constraints = [
            models.CheckConstraint(condition=models.Q(total__gte=0), name='pedido_total_no_negativo'),
        ]

    def puede_cambiar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES.get(self.estado, set())

    def __str__(self):
        return f'Pedido #{self.id} - {self.usuario.username}'


class ItemPedido(models.Model):
    """Copia del producto en el momento de la compra (nombre y precio congelados)."""
    id = models.BigAutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,           # si se borra el producto, el historial se conserva
        null=True,
        blank=True,
        related_name='items_pedido',
    )
    nombre = models.CharField(max_length=120)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'item_pedido'

    @property
    def subtotal(self):
        return self.precio * self.cantidad

    def __str__(self):
        return f'{self.cantidad} x {self.nombre}'
