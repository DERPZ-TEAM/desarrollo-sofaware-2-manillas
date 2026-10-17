# 📚 Documentación GoldBracelets — Índice y glosario

Esta carpeta explica **todo el proyecto de principio a fin**, pensada para personas que están aprendiendo. Cada documento puede leerse por separado, pero el orden de abajo va de lo general a lo particular.

| # | Documento | Qué aprendes |
|---|---|---|
| 01 | [Arquitectura y diagnóstico](01-arquitectura-y-diagnostico.md) | Cómo se conectan las piezas, qué errores tenía el proyecto y cómo se corrigieron (FASE 1) |
| 02 | [Base de datos y pgAdmin](02-base-de-datos.md) | Tablas, llaves primarias y foráneas, esquema SQL, conectar pgAdmin sin perder datos |
| 03 | [Seguridad, autenticación y CORS](03-seguridad-autenticacion-cors.md) | Login con JWT, roles admin/cliente, CORS Vercel↔Render, HTTPS (FASE 2) |
| 04 | [Backend explicado archivo por archivo](04-backend-codigo-explicado.md) | Qué hace cada archivo de Django y cada ruta de la API |
| 05 | [Variables de entorno](05-variables-de-entorno.md) | Lista limpia para local, Render y Vercel |
| 06 | [Despliegue](06-despliegue-render-vercel-supabase.md) | Paso a paso en Supabase, Render y Vercel |
| 07 | [Frontend y diseño UI/UX](07-frontend-y-diseno-ui.md) | Cómo está hecho React, paleta de colores y componentes (FASE 3) |
| 08 | [Sprints 1–5](08-sprints.md) | Qué se entregó en cada sprint con sus historias de usuario |
| 09 | [Guía de estudio](09-guia-de-estudio-preguntas.md) | Preguntas que puede hacer el profesor, con respuestas |
| — | [esquema.sql](esquema.sql) | Script SQL comentado de todas las tablas |

---

## Glosario (palabras que vas a ver mucho)

| Término | Explicación sencilla |
|---|---|
| **Frontend (FE)** | La parte que ve el usuario en el navegador: botones, pantallas, colores. Aquí es React. |
| **Backend (BE)** | El programa que corre en un servidor, guarda los datos y aplica las reglas. Aquí es Django. |
| **API** | "Menú" de operaciones que el backend ofrece al frontend. Ej.: `GET /api/productos/` devuelve los productos. |
| **REST** | Estilo de API que usa URLs para los recursos (`/productos/5/`) y verbos HTTP para la acción (GET leer, POST crear, PATCH editar, DELETE borrar). |
| **JSON** | Formato de texto para intercambiar datos: `{"nombre": "Pulsera", "precio": 185000}`. |
| **HTTP / HTTPS** | Protocolo con el que el navegador habla con los servidores. HTTPS = HTTP cifrado (candado 🔒). |
| **Endpoint / ruta** | Una URL concreta de la API, ej. `/api/auth/login/`. |
| **CRUD** | Create, Read, Update, Delete: crear, leer, actualizar y eliminar. |
| **Modelo (Django)** | Clase de Python que representa una tabla de la base de datos. |
| **Migración** | Archivo que describe un cambio en las tablas. `migrate` lo aplica en PostgreSQL. |
| **ORM** | Herramienta que traduce Python a SQL: `Producto.objects.filter(activo=True)` → `SELECT * FROM producto WHERE activo = true`. |
| **Serializer** | Convierte objetos Python ⇄ JSON y **valida** los datos que llegan. |
| **ViewSet / vista** | Función o clase que recibe una petición y devuelve una respuesta. |
| **PK (llave primaria)** | Columna que identifica cada fila de forma única (normalmente `id`). |
| **FK (llave foránea)** | Columna que guarda la PK de otra tabla para relacionarlas (ej. `producto.categoria_id`). |
| **JWT** | "JSON Web Token": un texto firmado que demuestra quién eres. Se envía en cada petición. |
| **Token access / refresh** | *access* dura 30 min y se usa en cada petición; *refresh* dura 1 día y sirve para pedir un nuevo access. |
| **CORS** | Regla del navegador: una página de un dominio (vercel.app) solo puede llamar a otro dominio (onrender.com) si este lo autoriza. |
| **Variable de entorno** | Valor de configuración que vive fuera del código (contraseñas, URLs). Se define en `.env` o en el panel de Render/Vercel. |
| **Deploy / despliegue** | Publicar la aplicación en internet. |
| **SPA** | "Single Page Application": la página se carga una vez y React cambia las pantallas sin recargar. |
| **Transacción atómica** | Grupo de operaciones en la BD que se hacen TODAS o NINGUNA. |
| **Hash de contraseña** | Transformación irreversible de la contraseña. La BD nunca guarda la clave real. |
| **Bucket** | "Carpeta" en la nube donde se guardan archivos (las fotos de los productos). |
| **Seed** | Datos iniciales de ejemplo (admin, cliente demo, categorías). |
