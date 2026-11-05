"""Registro de modelos en el panel interno /django-admin/ (herramienta de soporte)."""
from django.contrib import admin

from .models import Carrito, Categoria, Cliente, ItemCarrito, ItemPedido, Pedido, Perfil, Producto


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'tipo_documento', 'numero_documento', 'usuario', 'ciudad', 'eliminado_en')
    list_filter = ('tipo_documento', 'ciudad')
    search_fields = ('nombres', 'apellidos', 'numero_documento', 'correo', 'usuario__username')

    def get_queryset(self, request):
        return Cliente.todos.all()     # en el panel interno se ve también la papelera


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'orden', 'eliminado_en')
    search_fields = ('nombre',)

    def get_queryset(self, request):
        return Categoria.todos.all()


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('referencia', 'nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'activo', 'eliminado_en')
    list_filter = ('activo', 'categoria', 'tipo_pieza', 'tipo_oro', 'piedra')
    search_fields = ('referencia', 'nombre')

    def get_queryset(self, request):
        return Producto.todos.all()


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('producto', 'referencia', 'nombre', 'precio', 'cantidad')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'registrado_por', 'total', 'estado', 'metodo_pago', 'creado')
    list_filter = ('estado', 'metodo_pago')
    inlines = [ItemPedidoInline]


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'actualizado')
    inlines = [ItemCarritoInline]
