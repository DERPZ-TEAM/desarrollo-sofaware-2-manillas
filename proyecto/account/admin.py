from django.contrib import admin
from .models import Producto, Carrito, ItemCarrito, Categoria

admin.site.register(Producto)
admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Categoria)
