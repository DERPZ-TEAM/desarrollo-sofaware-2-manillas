"""Registro de modelos en el panel interno /django-admin/ (herramienta de soporte)."""
from django.contrib import admin

from .models import Carrito, Categoria, ItemCarrito, ItemPedido, Pedido, Perfil, Producto


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'ciudad')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'orden')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'activo')
    list_filter = ('activo', 'categoria', 'tipo_oro')
    search_fields = ('nombre',)


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('producto', 'nombre', 'precio', 'cantidad')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'total', 'estado', 'metodo_pago', 'creado')
    list_filter = ('estado', 'metodo_pago')
    inlines = [ItemPedidoInline]


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'actualizado')
    inlines = [ItemCarritoInline]
