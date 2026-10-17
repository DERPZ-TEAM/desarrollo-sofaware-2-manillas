"""
Mapa de rutas de la API. Todas cuelgan de /api/ (ver proyecto/urls.py).

El "router" de DRF genera solo las rutas del CRUD de los ViewSets.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import admin, auth, catalogo, salud_view, tienda

router = DefaultRouter()
router.register('categorias', catalogo.CategoriaViewSet, basename='categoria')
router.register('productos', catalogo.ProductoViewSet, basename='producto')
router.register('admin/pedidos', admin.PedidoAdminViewSet, basename='admin-pedido')

urlpatterns = [
    path('salud/', salud_view),

    # --- Autenticación ---
    path('auth/registro/', auth.registro_view),
    path('auth/login/', auth.login_view),
    path('auth/admin/login/', auth.admin_login_view),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/logout/', auth.logout_view),
    path('auth/me/', auth.me_view),
    path('auth/password/cambiar/', auth.cambiar_password_view),
    path('auth/password/recuperar/', auth.solicitar_recuperacion_view),
    path('auth/password/restablecer/', auth.confirmar_recuperacion_view),

    # --- Cliente ---
    path('carrito/', tienda.carrito_view),
    path('carrito/items/<int:item_id>/', tienda.item_carrito_view),
    path('checkout/', tienda.checkout_view),
    path('pedidos/', tienda.mis_pedidos_view),
    path('pedidos/<int:pedido_id>/', tienda.mi_pedido_detalle_view),
    path('pedidos/<int:pedido_id>/cancelar/', tienda.cancelar_mi_pedido_view),

    # --- Administrador ---
    path('admin/dashboard/', admin.dashboard_view),
    path('admin/clientes/', admin.clientes_admin_view),
    path('admin/inventario/', admin.inventario_view),
    path('admin/reportes/ingresos/', admin.reporte_ingresos_view),
    path('admin/reportes/mas-vendidos/', admin.reporte_mas_vendidos_view),
    path('admin/reportes/sin-ventas/', admin.reporte_sin_ventas_view),

    # --- CRUD automáticos (categorías, productos, pedidos admin) ---
    path('', include(router.urls)),
]
