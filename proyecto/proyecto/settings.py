"""
Configuración principal de Django para GoldBracelets.

Todas las claves sensibles (contraseñas, llaves secretas, URLs de la base de
datos) se leen desde VARIABLES DE ENTORNO. Así el mismo código funciona en:
  - Desarrollo local (lee el archivo proyecto/.env)
  - Producción en Render (lee las variables del panel "Environment")

Ver docs/05-variables-de-entorno.md para la lista completa.
"""
from datetime import timedelta
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. Lectura del archivo .env (solo para desarrollo local)
# ---------------------------------------------------------------------------
def cargar_archivo_env(ruta):
    """Lee líneas CLAVE=valor y las pone en os.environ si no existen ya.

    Usamos setdefault: si la variable ya está definida en el sistema
    (por ejemplo en Render), el valor del sistema tiene prioridad.
    """
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#') or '=' not in linea:
            continue
        clave, valor = linea.split('=', 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


cargar_archivo_env(BASE_DIR / '.env')


def env_bool(nombre, por_defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ('1', 'true', 'yes', 'si', 'on')


def env_lista(nombre, por_defecto=''):
    return [x.strip() for x in os.environ.get(nombre, por_defecto).split(',') if x.strip()]


# Render define automáticamente la variable RENDER=true en sus servidores.
EN_RENDER = env_bool('RENDER')


# ---------------------------------------------------------------------------
# 2. Seguridad básica
# ---------------------------------------------------------------------------
# DEBUG muestra errores detallados. NUNCA debe estar activo en producción.
# Si no se define DJANGO_DEBUG: activo en local, apagado en Render.
DEBUG = env_bool('DJANGO_DEBUG', por_defecto=not EN_RENDER)

CLAVE_LOCAL = 'clave-local-solo-para-desarrollo-no-usar-en-produccion'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', CLAVE_LOCAL)
if not DEBUG and SECRET_KEY == CLAVE_LOCAL:
    raise ImproperlyConfigured(
        'Falta DJANGO_SECRET_KEY. En producción es obligatoria una llave secreta propia.'
    )

ALLOWED_HOSTS = ['localhost', '127.0.0.1'] + env_lista('DJANGO_ALLOWED_HOSTS')
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')  # lo pone Render solo
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)


# ---------------------------------------------------------------------------
# 3. Aplicaciones y middleware
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Librerías externas
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # permite invalidar tokens al cerrar sesión
    'corsheaders',
    # Nuestra aplicación
    'account.apps.AccountConfig',
]

# El ORDEN importa: cada petición pasa por estas capas de arriba hacia abajo.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # sirve CSS/JS del admin en Render
    'corsheaders.middleware.CorsMiddleware',           # debe ir antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyecto.wsgi.application'


# ---------------------------------------------------------------------------
# 4. Base de datos (PostgreSQL)
# ---------------------------------------------------------------------------
def base_de_datos_desde_url(url):
    """Convierte una URL tipo postgresql://usuario:clave@host:puerto/nombre
    en el diccionario que Django necesita.

    Es la misma idea de la librería dj-database-url, escrita a mano para
    que se entienda qué hace.
    """
    partes = urlparse(url)
    if partes.scheme == 'sqlite':
        # sqlite:///ruta/archivo.db  (solo para pruebas rápidas)
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': unquote(partes.path[1:]) or str(BASE_DIR / 'db.sqlite3'),
        }
    if partes.scheme not in ('postgres', 'postgresql'):
        raise ImproperlyConfigured(f'Motor de base de datos no soportado: {partes.scheme}')

    opciones = {k: v[0] for k, v in parse_qs(partes.query).items()}
    host = partes.hostname or 'localhost'
    if host not in ('localhost', '127.0.0.1'):
        opciones.setdefault('sslmode', 'require')  # conexión cifrada hacia la nube
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(partes.path.lstrip('/')),
        'USER': unquote(partes.username or ''),
        'PASSWORD': unquote(partes.password or ''),
        'HOST': host,
        'PORT': str(partes.port or 5432),
        'OPTIONS': opciones,
        'CONN_MAX_AGE': 60,           # reutiliza conexiones (más rápido)
        'CONN_HEALTH_CHECKS': True,   # verifica que la conexión siga viva
    }


if os.environ.get('DATABASE_URL'):
    # Producción (Render / Supabase) o local si se define la URL completa
    DATABASES = {'default': base_de_datos_desde_url(os.environ['DATABASE_URL'])}
else:
    # Desarrollo local con PostgreSQL instalado en el equipo (pgAdmin)
    _host = os.environ.get('DB_HOST', 'localhost')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'goldbracelets'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': _host,
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {} if _host in ('localhost', '127.0.0.1') else {'sslmode': 'require'},
        }
    }


# ---------------------------------------------------------------------------
# 5. Contraseñas, idioma y zona horaria
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# 6. Archivos estáticos (CSS del admin) e imágenes de productos
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # aquí deja los archivos "collectstatic"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Supabase Storage: donde se guardan las fotos de los brazaletes en producción.
# El disco de Render se BORRA en cada despliegue, por eso no guardamos ahí.
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'imagenes-productos')
USAR_SUPABASE_STORAGE = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

STORAGES = {
    'default': {
        'BACKEND': (
            'account.storage.SupabaseStorage' if USAR_SUPABASE_STORAGE
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage' if not DEBUG
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

# Reglas para imágenes subidas por el administrador (HU-IN-009)
IMAGEN_MAX_MB = int(os.environ.get('IMAGEN_MAX_MB', '5'))
IMAGEN_FORMATOS = ('jpg', 'jpeg', 'png', 'webp')
DATA_UPLOAD_MAX_MEMORY_SIZE = (IMAGEN_MAX_MB + 1) * 1024 * 1024


# ---------------------------------------------------------------------------
# 7. CORS: qué páginas web (orígenes) pueden llamar a esta API
# ---------------------------------------------------------------------------
# Ejemplo en Render:
#   CORS_ALLOWED_ORIGINS=https://goldbracelets.vercel.app
#   CORS_ALLOWED_ORIGIN_REGEXES=^https://desarrollo-sofaware-2-manillas.*\.vercel\.app$
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
] + env_lista('CORS_ALLOWED_ORIGINS')
CORS_ALLOWED_ORIGIN_REGEXES = env_lista('CORS_ALLOWED_ORIGIN_REGEXES')
# Usamos tokens JWT en la cabecera Authorization (no cookies),
# por eso NO necesitamos enviar credenciales/cookies entre dominios.
CORS_ALLOW_CREDENTIALS = False
CORS_PREFLIGHT_MAX_AGE = 86400  # el navegador recuerda el permiso 24 h

# Para poder usar el admin de Django (/django-admin/) a través de HTTPS
CSRF_TRUSTED_ORIGINS = env_lista('CSRF_TRUSTED_ORIGINS')
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_HOST}')

# URL del frontend: se usa para armar el enlace de "recuperar contraseña"
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173').rstrip('/')


# ---------------------------------------------------------------------------
# 8. Django REST Framework + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Por defecto TODO exige estar autenticado; abrimos solo lo público.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        ('rest_framework.renderers.JSONRenderer',
         'rest_framework.renderers.BrowsableAPIRenderer') if DEBUG
        else ('rest_framework.renderers.JSONRenderer',)
    ),
    # Manejador global de errores: todas las respuestas de error tienen el mismo formato
    'EXCEPTION_HANDLER': 'account.exceptions.manejador_global_errores',
    # Límite de peticiones para frenar ataques de fuerza bruta
    'DEFAULT_THROTTLE_RATES': {
        'login': '10/minute',
        'recuperacion': '5/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_MINUTOS', '30'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_DIAS', '1'))),
    'ROTATE_REFRESH_TOKENS': True,       # cada renovación entrega un refresh nuevo
    'BLACKLIST_AFTER_ROTATION': True,    # y el anterior queda inválido
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# ---------------------------------------------------------------------------
# 9. Correo (recuperación de contraseña, HU-US-003)
# ---------------------------------------------------------------------------
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
else:
    # Sin servidor de correo: el mensaje se imprime en la consola/logs
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'GoldBracelets <no-reply@goldbracelets.com>')
# Solo para demostraciones: devuelve el enlace de recuperación en la respuesta.
MOSTRAR_ENLACE_RECUPERACION = env_bool('MOSTRAR_ENLACE_RECUPERACION', DEBUG)


# ---------------------------------------------------------------------------
# 10. Seguridad HTTPS (solo producción)
# ---------------------------------------------------------------------------
if not DEBUG:
    # Render recibe HTTPS y nos reenvía la petición; esta cabecera lo indica
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'


# ---------------------------------------------------------------------------
# 11. Registro de eventos (logs): se ven en la pestaña "Logs" de Render
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{levelname}] {asctime} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.db.backends': {'level': 'WARNING'},
    },
}
