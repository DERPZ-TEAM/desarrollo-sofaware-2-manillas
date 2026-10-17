"""
Rutas principales del backend.

  /               -> mensaje simple: la API está funcionando
  /api/...        -> la API REST que consume el frontend (React en Vercel)
  /django-admin/  -> panel interno de Django (solo superusuarios)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def inicio(request):
    return JsonResponse({
        'proyecto': 'GoldBracelets API',
        'estado': 'funcionando',
        'documentacion': 'Ver carpeta docs/ del repositorio',
        'api': request.build_absolute_uri('/api/'),
    })


urlpatterns = [
    path('', inicio),
    path('django-admin/', admin.site.urls),
    path('api/', include('account.urls')),
]

if settings.DEBUG:
    # En local, Django sirve las imágenes subidas. En producción las sirve Supabase.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
