"""
URL configuration for proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from account import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('inicio/', views.inicio, name='inicio'),
    path('logout/', views.cerrar_sesion, name='logout'),

    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='account/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='account/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='account/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset_done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='account/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path(
        'actualizar_usuario/',
        views.actualizar_usuario,
        name='actualizar_usuario'
    ),
    path(
        'agregar_carrito/<int:producto_id>/',
        views.agregar_carrito,
        name='agregar_carrito'
    ),
    path(
        'carrito/',
        views.ver_carrito,
        name='carrito'
    ),
    path(
        'eliminar_item/<int:item_id>/',
        views.eliminar_item,
        name='eliminar_item'
    ),
    path(
        'aumentar/<int:item_id>/',
        views.aumentar_cantidad,
        name='aumentar_cantidad'
    ),

    path(
        'disminuir/<int:item_id>/',
        views.disminuir_cantidad,
        name='disminuir_cantidad'
    ),

    path(
        'vaciar_carrito/',
        views.vaciar_carrito,
        name='vaciar_carrito'
    ),

    path(
        'finalizar_compra/',
        views.finalizar_compra,
        name='finalizar_compra'
    ),

    # --- Gestión de productos (administrador) ---
    path(
        'productos/',
        views.gestion_productos,
        name='gestion_productos'
    ),
    path(
        'productos/nuevo/',
        views.registrar_producto,
        name='registrar_producto'
    ),
    path(
        'productos/<int:producto_id>/editar/',
        views.editar_producto,
        name='editar_producto'
    ),
    path(
        'productos/<int:producto_id>/eliminar/',
        views.eliminar_producto,
        name='eliminar_producto'
    ),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
