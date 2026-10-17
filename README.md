# GoldBracelets · Tienda virtual de joyería en oro

Proyecto del curso **750021C – Desarrollo de Software II** (Universidad del Valle, sede Yumbo) – Grupo 2.

| Integrante | Código |
|---|---|
| Deiby Jair Portillo Ordoñez | 202360316 |
| Johan Stuar Lozano Ruiz | 202360136 |
| Sebastian Carvajal Lopez | 202369157 |
| Sebastian Londoño Vásquez | 202360397 |

Tienda web con **dos flujos de usuario independientes**:

- **Cliente**: ve el catálogo de brazaletes, busca y filtra, agrega al carrito, compra (envío + método de pago), descarga su comprobante y gestiona su perfil.
- **Administrador**: panel privado con CRUD de productos (precios, stock, imágenes), categorías, inventario con alertas, gestión de pedidos (estados y guía de envío), clientes y reportes de ventas.

## Tecnologías

| Capa | Tecnología | Dónde se publica |
|---|---|---|
| Frontend (FE) | React 18 + Vite + React Router | **Vercel** |
| Backend (BE) | Python · Django 5/6 + Django REST Framework + JWT | **Render** |
| Base de datos (BD) | PostgreSQL | **Supabase** (o Render PostgreSQL) |
| Imágenes | Supabase Storage (bucket `imagenes-productos`) | Supabase |
| Administración de la BD | pgAdmin 4 | equipo local |

```
Navegador ──HTTPS──► Vercel (React) ──HTTPS + JSON + JWT──► Render (Django API) ──SSL──► PostgreSQL (Supabase)
                                                                   └──────HTTPS──────► Supabase Storage (fotos)
```

## Estructura del repositorio

```
django123456/
├── frontend/                 # Aplicación React (lo que ve el usuario)
│   ├── src/
│   │   ├── api/client.js     # Todas las llamadas HTTP a la API
│   │   ├── context/          # Sesión del usuario (AuthContext)
│   │   ├── components/       # Piezas reutilizables (tarjetas, modales, alertas)
│   │   ├── layouts/          # Estructura de la tienda y del panel admin
│   │   ├── pages/store/      # Pantallas del CLIENTE
│   │   ├── pages/admin/      # Pantallas del ADMINISTRADOR
│   │   └── styles.css        # Sistema de diseño (colores, tipografías)
│   └── vercel.json           # Configuración de Vercel (rutas de la SPA)
├── proyecto/                 # Backend Django (la API)
│   ├── proyecto/settings.py  # Configuración (BD, CORS, JWT, seguridad)
│   ├── account/              # Nuestra app: modelos, API, lógica de negocio
│   │   ├── models.py         # Tablas de la base de datos
│   │   ├── serializers.py    # Validación de datos y formato JSON
│   │   ├── services.py       # Reglas del negocio (stock, descuentos, pedidos)
│   │   ├── views/            # Rutas de la API separadas por módulo
│   │   ├── permissions.py    # Quién puede hacer qué (admin / cliente)
│   │   ├── exceptions.py     # Manejo global de errores
│   │   ├── storage.py        # Subida de imágenes a Supabase
│   │   └── tests/            # Pruebas automáticas
│   ├── build.sh              # Script de construcción para Render
│   └── requirements.txt      # Librerías de Python
├── docs/                     # 📚 DOCUMENTACIÓN COMPLETA (empieza aquí)
├── render.yaml               # Blueprint de Render
└── supabase/                 # Configuración del proyecto Supabase
```

## Documentación

Toda la explicación paso a paso está en [`docs/`](docs/00-indice.md). Orden recomendado de estudio:

1. [Índice y glosario](docs/00-indice.md)
2. [Arquitectura y diagnóstico](docs/01-arquitectura-y-diagnostico.md)
3. [Base de datos y pgAdmin](docs/02-base-de-datos.md)
4. [Seguridad, login y CORS](docs/03-seguridad-autenticacion-cors.md)
5. [Backend explicado archivo por archivo](docs/04-backend-codigo-explicado.md)
6. [Variables de entorno](docs/05-variables-de-entorno.md)
7. [Despliegue en Render, Vercel y Supabase](docs/06-despliegue-render-vercel-supabase.md)
8. [Frontend y diseño UI/UX](docs/07-frontend-y-diseno-ui.md)
9. [Sprints 1 a 5](docs/08-sprints.md)
10. [Guía de estudio para la sustentación](docs/09-guia-de-estudio-preguntas.md)

## Inicio rápido (local)

Requisitos: Python 3.12+, Node 20+, PostgreSQL (pgAdmin).

```bash
cd proyecto
python -m venv .venv
.venv\Scripts\activate          # Windows  (en Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # y edita DB_PASSWORD con tu clave de PostgreSQL
python manage.py migrate
python manage.py seed_goldbracelets
python manage.py runserver
```

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173 · Cliente demo: `cliente` / `Cliente123` · Admin: `admin` / `AdminGold123` (entra por `/admin/ingresar`).

Pruebas automáticas del backend: `python manage.py test account` (24 pruebas).
