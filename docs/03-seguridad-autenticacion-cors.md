# 03 · Seguridad, autenticación (JWT) y CORS (FASE 2)

## 1. ¿Por qué JWT y no sesiones con cookies?

El frontend (`*.vercel.app`) y el backend (`*.onrender.com`) están en **dominios distintos**. Las cookies de sesión entre dominios dan muchos problemas (SameSite, CSRF, bloqueos de navegadores). Con **JWT** el backend no guarda sesiones: entrega un token firmado y el frontend lo envía en cada petición en la cabecera:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo1LCJyb2wiOiJjbGllbnRlIn0.firma
```

Un JWT tiene 3 partes separadas por puntos: **cabecera** (algoritmo), **contenido** (`user_id`, `rol`, fecha de vencimiento) y **firma** (hecha con `DJANGO_SECRET_KEY`). Si alguien cambia el contenido (por ejemplo pone `rol: admin`), la firma ya no coincide y el backend lo rechaza. Por eso la `DJANGO_SECRET_KEY` debe ser secreta.

## 2. Flujo de inicio de sesión

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as React (Vercel)
    participant BE as Django (Render)
    participant DB as PostgreSQL
    U->>FE: escribe usuario/correo + contraseña
    FE->>BE: POST /api/auth/login/  {username, password}
    BE->>DB: busca el usuario y compara el HASH de la contraseña
    alt credenciales correctas y es cliente
        BE-->>FE: 200 {access (30 min), refresh (1 día), user{rol:"cliente"}}
        FE->>FE: guarda tokens en localStorage
    else contraseña incorrecta
        BE-->>FE: 401 "Usuario o contraseña incorrectos."
    else es admin intentando entrar por la tienda
        BE-->>FE: 403 "Las cuentas de administrador ingresan por el panel"
    end
    Note over FE,BE: Peticiones siguientes
    FE->>BE: GET /api/carrito/  Authorization: Bearer <access>
    BE-->>FE: 200 carrito
    Note over FE,BE: 30 minutos después el access vence
    FE->>BE: GET /api/pedidos/ (access vencido)
    BE-->>FE: 401
    FE->>BE: POST /api/auth/refresh/ {refresh}
    BE-->>FE: 200 {access nuevo, refresh nuevo} (el refresh viejo queda en lista negra)
    FE->>BE: repite GET /api/pedidos/ ✔
```

### Dos puertas de entrada independientes
| Flujo | Pantalla | Endpoint | Quién puede entrar |
|---|---|---|---|
| Cliente | `/ingresar` | `POST /api/auth/login/` | Solo `rol = cliente` |
| Administrador | `/admin/ingresar` | `POST /api/auth/admin/login/` | Solo `rol = admin` |

Código: `proyecto/account/views/auth.py`, función `_login(request, solo_admin)`.

### Cierre de sesión (HU-SE-032)
- **Manual**: botón *Salir* → `POST /api/auth/logout/` pone el refresh en la **lista negra** (tabla `token_blacklist_blacklistedtoken`); aunque alguien lo hubiera copiado, ya no sirve.
- **Automático por inactividad**: `AuthContext.jsx` cierra la sesión tras 30 minutos sin clics ni teclas.
- **Por vencimiento**: si el refresh venció (1 día), el frontend muestra "Tu sesión expiró".

### Recuperación de contraseña (HU-US-003)
1. `POST /api/auth/password/recuperar/ {email}` → Django genera un **token de un solo uso** (`default_token_generator`) que deja de servir apenas se cambia la contraseña.
2. Se envía al correo un enlace `https://<frontend>/restablecer/<uid>/<token>`.
3. La pantalla `ResetPassword.jsx` envía `{uid, token, password, password2}` a `/api/auth/password/restablecer/`.
4. Sin servidor de correo configurado (por ejemplo en la demo), si `MOSTRAR_ENLACE_RECUPERACION=True` la API devuelve el enlace para poder probarlo.

### Límite de intentos (fuerza bruta)
`settings.py → DEFAULT_THROTTLE_RATES`: máximo **10 logins por minuto** y **5 recuperaciones por hora** por IP. Después responde 429.

## 3. Cómo el backend decide si eres Admin o Cliente

`proyecto/account/permissions.py`:

```python
def es_admin(user):
    if not (user and user.is_authenticated):
        return False
    perfil = getattr(user, 'perfil', None)
    if perfil is not None:
        return perfil.rol == Perfil.ROL_ADMIN
    return user.is_staff


class EsAdministrador(BasePermission):
    message = 'Solo el administrador puede realizar esta acción.'
    def has_permission(self, request, view):
        return es_admin(request.user)


class EsCliente(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not es_admin(user))


class LecturaPublicaEscrituraAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:   # GET, HEAD, OPTIONS
            return True
        return es_admin(request.user)
```

Y se aplican en cada vista:

```python
@api_view(['GET'])
@permission_classes([EsAdministrador])      # 👈 solo admin
def dashboard_view(request): ...

@api_view(['POST'])
@permission_classes([EsCliente])            # 👈 solo clientes (el admin no compra)
def checkout_view(request): ...

class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [LecturaPublicaEscrituraAdmin]   # 👈 todos leen, solo admin escribe
```

**Orden de las validaciones en cada petición:**
1. ¿Hay token? Si la ruta lo exige y no hay → **401**.
2. ¿El token es válido y no ha vencido? (firma con `SECRET_KEY`) Si no → **401**.
3. ¿El rol tiene permiso? Si no → **403** con el mensaje del permiso.
4. Solo entonces se ejecuta la vista.

> ⚠️ En el frontend también existen "guardias" (`components/ProtectedRoute.jsx`) que redirigen al login correcto, pero **son solo comodidad**. La seguridad real está en el backend: aunque alguien edite el `localStorage` y ponga `rol: admin`, la API lo rechaza porque el token firmado dice otra cosa.

## 4. CORS: comunicación limpia entre Vercel y Render

**¿Qué es?** Por seguridad, el navegador no deja que JavaScript de `https://goldbracelets.vercel.app` lea respuestas de `https://api.onrender.com` a menos que el servidor responda con la cabecera `Access-Control-Allow-Origin: https://goldbracelets.vercel.app`. Antes de un POST con JSON o con `Authorization`, el navegador hace una petición previa **OPTIONS** ("preflight") para preguntar si está permitido.

**Código exacto** (`proyecto/proyecto/settings.py`):

```python
INSTALLED_APPS = [..., 'corsheaders', ...]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',        # ⚠️ ANTES de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
] + env_lista('CORS_ALLOWED_ORIGINS')          # ej. https://goldbracelets.vercel.app
CORS_ALLOWED_ORIGIN_REGEXES = env_lista('CORS_ALLOWED_ORIGIN_REGEXES')
# ej. ^https://desarrollo-sofaware-2-manillas.*\.vercel\.app$  (cubre las "preview" de Vercel)
CORS_ALLOW_CREDENTIALS = False   # usamos JWT en cabecera, no cookies
CORS_PREFLIGHT_MAX_AGE = 86400   # el navegador recuerda el permiso 24 h
```

**Variables en Render** (ver [05-variables-de-entorno.md](05-variables-de-entorno.md)):
```
CORS_ALLOWED_ORIGINS=https://goldbracelets.vercel.app
CORS_ALLOWED_ORIGIN_REGEXES=^https://desarrollo-sofaware-2-manillas.*\.vercel\.app$
```

**Errores típicos y su solución:**

| Mensaje en la consola del navegador | Causa | Solución |
|---|---|---|
| `blocked by CORS policy: No 'Access-Control-Allow-Origin'` | El dominio de Vercel no está en `CORS_ALLOWED_ORIGINS` | Agregarlo **exacto**: con `https://`, sin `/` al final |
| CORS error pero en Render el log dice 500 | El backend falló y la respuesta de error no trae cabeceras | Revisar el log de Render; corregir el error real |
| `Mixed Content: ... requested an insecure resource 'http://...'` | `VITE_API_URL` empieza por `http://` | Usar `https://...onrender.com/api` |
| 404 en `/api/api/...` | `VITE_API_URL` terminado en `/api/` y el código agrega `/api` | Usar exactamente `https://<servicio>.onrender.com/api` |
| La primera petición tarda ~50 s | Render gratis "duerme" el servicio tras 15 min sin uso | Normal en plan gratis; abrir `/api/salud/` antes de la demo |

## 5. Check de seguridad inicial

### Base de datos
- [x] Conexión con **SSL obligatorio** (`sslmode=require`, puesto automáticamente en `settings.py` para hosts remotos).
- [x] Credenciales solo en variables de entorno; `.env` está en `.gitignore`.
- [x] Contraseñas de usuarios con **hash** PBKDF2 (Django) + validadores (mínimo 8, no comunes, no solo números, no parecida al usuario).
- [x] El ORM usa **consultas parametrizadas** → protegido contra inyección SQL.
- [x] Restricciones en la BD (FK, UNIQUE, CHECK) como segunda barrera.
- [ ] Recomendado: usuario de solo lectura para pgAdmin (ver doc 02) y no compartir la clave de `postgres`.
- [ ] Recomendado: en Supabase activar *Network Restrictions* si el plan lo permite.

### Backend
- [x] `DEBUG=False` en producción (automático en Render) y `DJANGO_SECRET_KEY` obligatoria.
- [x] `ALLOWED_HOSTS` restringido (Render agrega su dominio solo).
- [x] HTTPS forzado: `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, HSTS, cookies `Secure`.
- [x] Cabeceras: `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`.
- [x] Tokens cortos (30 min) + rotación + lista negra.
- [x] Límite de intentos de login.
- [x] Validación de imágenes: solo JPG/PNG/WEBP, máximo 5 MB, y Pillow verifica que realmente sea una imagen.
- [x] La **service key** de Supabase solo vive en Render (nunca en el frontend).

### Frontend / contenido mixto (HTTPS/HTTP)
- **Contenido mixto** = una página cargada por HTTPS que pide algo por HTTP. El navegador lo bloquea. Para evitarlo **todas** las URLs deben ser `https://`: Vercel ✔, Render ✔, Supabase ✔ (`VITE_API_URL` y `SUPABASE_URL` deben empezar con `https://`).
- React escapa automáticamente el texto → protección contra XSS.
- `vercel.json` agrega cabeceras de seguridad.
- Nota: los tokens se guardan en `localStorage` (simple y adecuado para el proyecto). La alternativa más segura en sistemas grandes es una cookie `HttpOnly` en el mismo dominio.
