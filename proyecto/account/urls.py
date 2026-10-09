from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register('categorias', views.CategoriaViewSet, basename='categoria')
router.register('productos', views.ProductoViewSet, basename='producto')
router.register('admin/pedidos', views.PedidoAdminViewSet, basename='admin-pedido')

urlpatterns = [
    path('auth/registro/', views.registro_view),
    path('auth/login/', views.login_view),
    path('auth/admin/login/', views.admin_login_view),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/me/', views.me_view),
    path('carrito/', views.carrito_view),
    path('carrito/items/<int:item_id>/', views.item_carrito_view),
    path('checkout/', views.checkout_view),
    path('pedidos/', views.mis_pedidos_view),
    path('admin/dashboard/', views.dashboard_view),
    path('admin/clientes/', views.clientes_admin_view),
    path('', include(router.urls)),
]
