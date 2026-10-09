from django.db import models
from django.contrib.auth.models import User


from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/')
    activo = models.BooleanField(default=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )

    def __str__(self):
        return self.nombre


class Carrito(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.usuario.username


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField(default=1)
