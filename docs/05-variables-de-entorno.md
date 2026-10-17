# 05 · Variables de entorno

Una **variable de entorno** es un dato de configuración que vive **fuera del código**. Así:
- Las contraseñas no quedan en GitHub.
- El mismo código funciona en local y en producción cambiando solo las variables.

Dónde se escriben:
- **Local backend**: archivo `proyecto/.env` (copiar de `proyecto/.env.example`). Está en `.gitignore`.
- **Local frontend**: no hace falta nada (Vite redirige `/api` al backend local).
- **Render**: servicio → **Environment** → *Add Environment Variable*.
- **Vercel**: proyecto → **Settings → Environment Variables**.

## Backend (Django)

| Variable | Local (`proyecto/.env`) | Producción (Render) | Obligatoria | Descripción |
|---|---|---|---|---|
| `DJANGO_DEBUG` | `True` | `False` (o no ponerla: en Render se apaga sola) | No | Muestra errores detallados. Nunca `True` en producción |
| `DJANGO_SECRET_KEY` | cualquier texto | texto largo aleatorio (Render: *Generate*) | **Sí en prod** | Firma los JWT y protege la app. Si se filtra, hay que cambiarla |
| `DATABASE_URL` | (opcional) | `postgresql://postgres.xxxx:CLAVE@aws-0-REGION.pooler.supabase.com:5432/postgres` | **Sí en prod** | Conexión a PostgreSQL. Tiene prioridad sobre las `DB_*` |
| `DB_NAME` | `goldbracelets` | — | Local | Nombre de la BD local (pgAdmin) |
| `DB_USER` | `postgres` | — | Local | Usuario de PostgreSQL local |
| `DB_PASSWORD` | tu clave | — | Local | Clave de PostgreSQL local |
| `DB_HOST` | `localhost` | — | Local | — |
| `DB_PORT` | `5432` | — | Local | — |
| `DJANGO_ALLOWED_HOSTS` | — | (opcional) dominios extra separados por coma | No | Render agrega su dominio solo (`RENDER_EXTERNAL_HOSTNAME`) |
| `CORS_ALLOWED_ORIGINS` | — | `https://goldbracelets.vercel.app` | **Sí en prod** | URL(s) exactas del frontend, separadas por coma, sin `/` final |
| `CORS_ALLOWED_ORIGIN_REGEXES` | — | `^https://desarrollo-sofaware-2-manillas.*\.vercel\.app$` | No | Para permitir las URLs de *preview* de Vercel |
| `CSRF_TRUSTED_ORIGINS` | — | (opcional) | No | Solo si se usa `/django-admin/` desde otro dominio |
| `FRONTEND_URL` | `http://localhost:5173` | `https://goldbracelets.vercel.app` | Sí en prod | Para armar el enlace de "recuperar contraseña" |
| `SUPABASE_URL` | (vacío = disco local) | `https://sxuavqduvjlcwioijotz.supabase.co` | **Sí en prod** | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | (vacío) | *service_role key* de Supabase | **Sí en prod** | Permite subir/borrar fotos. ⚠️ **Secreta**: solo en Render, jamás en el frontend |
| `SUPABASE_BUCKET` | `imagenes-productos` | `imagenes-productos` | No | Nombre del bucket público |
| `IMAGEN_MAX_MB` | `5` | `5` | No | Tamaño máximo de imagen |
| `JWT_ACCESS_MINUTOS` | `30` | `30` | No | Duración del token access |
| `JWT_REFRESH_DIAS` | `1` | `1` | No | Duración del token refresh |
| `SEED_ADMIN_PASSWORD` | — | clave fuerte para el usuario `admin` | Recomendada | Si existe, el seed fija esa clave al admin en cada despliegue |
| `SEED_CLIENTE_PASSWORD` | — | (opcional) | No | Clave del cliente demo al crearlo |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | — | ej. Gmail: `smtp.gmail.com`, `587`, correo, *contraseña de aplicación*, `True` | No | Para enviar correos reales de recuperación |
| `DEFAULT_FROM_EMAIL` | — | `GoldBracelets <tucorreo@gmail.com>` | No | Remitente |
| `MOSTRAR_ENLACE_RECUPERACION` | `True` (automático con DEBUG) | `True` solo para la demo sin correo | No | Devuelve el enlace de recuperación en la respuesta |
| `PYTHON_VERSION` | — | `3.12.7` | Recomendada | Versión de Python en Render |
| `RENDER`, `RENDER_EXTERNAL_HOSTNAME` | — | **las pone Render solo** | — | No crearlas a mano |

## Frontend (React / Vite)

| Variable | Local | Producción (Vercel) | Descripción |
|---|---|---|---|
| `VITE_API_URL` | (vacía → usa `/api` con el proxy de Vite) | `https://desarrollo-sofaware-2-manillas.onrender.com/api` | URL base de la API. Debe empezar por **https://** y terminar en `/api` (sin `/` final) |

> ⚠️ Todo lo que empieza por `VITE_` queda **visible** dentro del JavaScript que descarga el navegador. Nunca pongas claves secretas en variables `VITE_`.
>
> Las variables de Vite se leen **al compilar** (`npm run build`). Si cambias `VITE_API_URL` en Vercel debes hacer **Redeploy**.

El archivo `frontend/.env.production` del repositorio contiene la URL pública de Render (no es secreta). Si se define la variable en el panel de Vercel, esa tiene prioridad.

## Plantillas

`proyecto/.env` (local):
```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria
DB_NAME=goldbracelets
DB_USER=postgres
DB_PASSWORD=tu_clave_de_postgres
DB_HOST=localhost
DB_PORT=5432
FRONTEND_URL=http://localhost:5173
```

Render (producción):
```env
PYTHON_VERSION=3.12.7
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generada por Render>
DATABASE_URL=postgresql://postgres.<ref>:<clave>@aws-0-<region>.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://sxuavqduvjlcwioijotz.supabase.co
SUPABASE_SERVICE_KEY=<service_role key>
SUPABASE_BUCKET=imagenes-productos
CORS_ALLOWED_ORIGINS=https://<tu-proyecto>.vercel.app
CORS_ALLOWED_ORIGIN_REGEXES=^https://desarrollo-sofaware-2-manillas.*\.vercel\.app$
FRONTEND_URL=https://<tu-proyecto>.vercel.app
SEED_ADMIN_PASSWORD=<clave fuerte>
MOSTRAR_ENLACE_RECUPERACION=True
```

Vercel:
```env
VITE_API_URL=https://desarrollo-sofaware-2-manillas.onrender.com/api
```

## Generar una SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
