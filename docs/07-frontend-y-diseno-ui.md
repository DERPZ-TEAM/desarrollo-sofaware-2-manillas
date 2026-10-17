# 07 · Frontend (React) y diseño UI/UX (FASE 3)

## 1. ¿Cómo funciona el frontend?

Es una **SPA** (*Single Page Application*) hecha con **React 18** y empaquetada con **Vite**:
- El navegador descarga **una sola vez** `index.html` + un archivo JavaScript.
- **React Router** cambia de pantalla según la URL sin recargar la página.
- Los datos se piden a la API con `fetch` y se guardan en el **estado** de cada componente (`useState`).

```
frontend/src/
├── main.jsx               # Punto de entrada: monta <App/> dentro de <BrowserRouter> y <AuthProvider>
├── App.jsx                # Mapa de rutas → qué pantalla se muestra en cada URL
├── styles.css             # Sistema de diseño (todas las clases y colores)
├── api/client.js          # Única puerta de salida hacia la API
├── context/AuthContext.jsx# Sesión: usuario actual, login, logout, contador del carrito
├── utils/
│   ├── format.js          # money(), fecha(), estados de pedido, imagen de respaldo
│   └── useAddToCart.js    # Hook reutilizable del botón "Añadir"
├── components/
│   ├── ui.jsx             # Alert, Loader, EmptyState, Field, Modal, StatusBadge
│   ├── ProductCard.jsx    # Tarjeta de producto
│   ├── AuthShell.jsx      # Marco de las pantallas de login/registro
│   └── ProtectedRoute.jsx # RequireCustomer / RequireAdmin
├── layouts/
│   ├── StoreLayout.jsx    # Barra, menú y pie de la TIENDA
│   └── AdminLayout.jsx    # Menú lateral y cabecera del PANEL
└── pages/
    ├── store/  Home, Catalog, Product, Cart, Checkout, OrderDetail, Profile,
    │           Login, Register, ForgotPassword, ResetPassword, NotFound
    └── admin/  AdminLogin, Dashboard, AdminProducts, AdminCategories,
                AdminInventory, AdminOrders, AdminClients, AdminReports
```

### 1.1 Mapa de pantallas

| URL | Pantalla | Quién | Historia |
|---|---|---|---|
| `/` | Portada (landing) | Todos | HU-VE-011 |
| `/catalogo` | Catálogo con búsqueda y filtros | Todos | HU-VE-011, 013, 014, 015, HU-IN-049 |
| `/producto/:id` | Detalle + ficha técnica | Todos | HU-VE-12, HU-PR-035 |
| `/ingresar`, `/registro` | Login / registro de clientes | Visitantes | HU-AU-002, HU-US-001 |
| `/recuperar`, `/restablecer/:uid/:token` | Recuperar contraseña | Visitantes | HU-US-003 |
| `/carrito` | Carrito con totales y descuentos | Cliente | HU-CO-016, 017, 018 |
| `/checkout` | Envío + método de pago | Cliente | HU-VE-019, 020, 021 |
| `/pedido/:id` | Comprobante imprimible | Cliente | HU-VE-022, HU-PE-023 |
| `/cuenta` | Mis pedidos, mis datos, contraseña | Cliente | HU-US-004, HU-PE-023 |
| `/admin/ingresar` | Login del administrador | Admin | HU-AU-002 |
| `/admin` | Escritorio | Admin | HU-IN-048 |
| `/admin/productos` | CRUD de productos con imagen | Admin | HU-IN-006…010 |
| `/admin/categorias` | CRUD de categorías | Admin | HU-IN-010 |
| `/admin/inventario` | Stock, valor y alertas | Admin | HU-IN-028, 048 |
| `/admin/pedidos` | Pedidos, estados y guía | Admin | HU-PE-024, 025, 050 |
| `/admin/clientes` | Clientes en orden alfabético | Admin | HU-US-005 |
| `/admin/reportes` | Ingresos, más vendidos, sin ventas | Admin | HU-RE-030, 031, 045, 046 |

### 1.2 `api/client.js` — cómo se habla con el backend

```js
export const API_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export async function api(path, { method = 'GET', body, auth = true, retry = true } = {}) {
  // 1. arma cabeceras: JSON + Authorization: Bearer <token>
  // 2. hace fetch(API_URL + path)
  // 3. si responde 401 y hay refresh token → lo renueva y REPITE la petición una vez
  // 4. si hay error → lanza ApiError con el mensaje "detail" del backend y los errores por campo
}
```
- Si `body` es un `FormData` (formulario con imagen) no se convierte a JSON: el navegador lo envía como *multipart*.
- Si varias peticiones fallan a la vez por token vencido, se hace **una sola** renovación (variable `refreshing`).
- Sin internet → mensaje "No hay conexión con el servidor".

### 1.3 `AuthContext.jsx` — la sesión
Un **Context** de React es un "almacén global": cualquier pantalla hace `const { user, isAdmin, login, logout } = useAuth()`. Además:
- Guarda los tokens en `localStorage` (sobreviven a recargar la página).
- Cierra sesión tras **30 minutos de inactividad** escuchando clics, teclas y scroll.
- Mantiene el número del icono del carrito.

### 1.4 Patrón de cada pantalla
Casi todas siguen el mismo esquema, fácil de explicar:
```jsx
const [datos, setDatos] = useState(null)        // null = cargando
const [error, setError] = useState('')

useEffect(() => {                                // al abrir la pantalla...
  api('/admin/dashboard/').then(setDatos).catch((e) => setError(e.message))
}, [])

if (error) return <Alert>{error}</Alert>
if (!datos) return <Loader />
return <>...pintar datos...</>
```
Así se cumplen los criterios "mostrar mensaje si falla la conexión" y "no mostrar información incompleta".

## 2. Diseño visual (UI) — marca de lujo "GoldBracelets"

### 2.1 Paleta de colores
Definida una sola vez como variables CSS en `styles.css` (`:root`):

| Token | Color | Uso |
|---|---|---|
| `--ink` | `#0F0E0C` ⬛ | Negro profundo: barra superior, hero, menú del panel, botones principales |
| `--ink-2` / `--ink-3` | `#1B1915` / `#2A2721` | Variaciones para profundidad (degradados) |
| `--gold` | `#C9A45C` 🟨 | Dorado de marca: botón principal, acentos, anillos |
| `--gold-deep` | `#A8843F` | Dorado oscuro: textos dorados legibles, *hover* |
| `--gold-soft` | `#EFE3C6` | Dorado muy claro: fondos de avisos |
| `--ivory` | `#FAF7F1` | Marfil: fondo general (más cálido y elegante que blanco puro) |
| `--white` | `#FFFFFF` | Tarjetas y formularios |
| `--muted` | `#7A7266` | Textos secundarios |
| `--line` | `#E8E1D3` | Bordes suaves |
| Estados | verde `#2F6B4F`, ámbar `#9A6A12`, rojo `#A33B3B`, azul `#3A5A7A` | Éxito, advertencia, error, información (con fondos claros) |

**Regla 60-30-10:** 60 % marfil/blanco (respira), 30 % negro (elegancia y contraste), 10 % dorado (solo para lo importante: precios, botones de compra, elementos activos). Si todo fuera dorado, nada destacaría.

### 2.2 Tipografías (Google Fonts)
- **Cormorant Garamond** (serif, con remates): títulos, nombres de productos, precios grandes. Transmite tradición y lujo (como las marcas de joyería clásicas).
- **Outfit** (sans-serif geométrica): textos, botones, tablas. Moderna y muy legible en pantallas pequeñas.
- Detalles de lujo: letras con espaciado amplio (`letter-spacing`) en mayúsculas para etiquetas (`.eyebrow`), títulos en *itálica dorada* ("cada *detalle*").

### 2.3 Sombras, bordes y movimiento
- Bordes redondeados de 14 px (`--radius`) y botones tipo píldora.
- Sombras suaves en capas (`--shadow-sm`, `--shadow`) y una sombra dorada para el botón principal (`--shadow-gold`).
- Micro-animaciones: tarjetas que suben 4 px al pasar el mouse, zoom suave de la foto, botones que se elevan 1 px.
- Anillos dorados dibujados solo con CSS en el *hero* y en el login (no requieren imágenes).

### 2.4 Componentes clave — vista del CLIENTE
1. **Barra superior** negra con mensajes de confianza (envíos, descuentos, compra segura).
2. **Navegación** fija con efecto vidrio (`backdrop-filter: blur`), logo circular dorado "GB" y contador del carrito.
3. **Hero (landing)**: degradado negro con resplandor dorado, título serif grande, dos llamados a la acción.
4. **Franja de beneficios** flotando sobre el hero (oro certificado, hecho a mano, precio por mayor, envío).
5. **Mosaico de colecciones** (categorías con su conteo de piezas).
6. **Tarjeta de producto sofisticada**: foto cuadrada con zoom, cinta "Agotado"/"Últimas unidades", categoría en mayúsculas espaciadas, nombre serif, especificaciones (oro · quilates · talla), precio y botón dorado.
7. **Catálogo** con panel de filtros fijo (chips de categoría, rango de precio, tipo de oro, talla, orden).
8. **Detalle** a dos columnas con **ficha técnica** en tarjeta.
9. **Carrito** con resumen lateral fijo, descuento en dorado y mensaje "agrega N piezas para más descuento".
10. **Checkout** en pasos (1. Envío, 2. Pago) con opciones de pago tipo tarjeta seleccionable.
11. **Comprobante** con línea de seguimiento (pendiente → confirmado → enviado → entregado) y estilo de impresión.

### 2.5 Componentes clave — vista del ADMINISTRADOR
1. **Menú lateral negro** con íconos dorados y el elemento activo resaltado con una barra dorada; en celular se oculta y se abre con ☰.
2. **Tarjetas de indicadores** (ventas totales destacada en negro/dorado, ventas del mes, pedidos, clientes, productos, unidades).
3. **Tablas organizadas**: encabezados en mayúsculas pequeñas, filas con *hover*, miniatura del producto, **insignias de estado** de colores (Pendiente ámbar, Confirmado azul, Enviado dorado, Entregado verde, Cancelado rojo).
4. **Barra de herramientas** con búsqueda y filtros sobre cada tabla.
5. **Formularios modernos en ventana modal**: dos columnas (datos | imagen con vista previa), sección "Ficha técnica", mensajes de error bajo cada campo, interruptor "Visible en la tienda".
6. **Gráfico de barras** en CSS puro para ingresos por periodo (sin librerías).
7. **Estados vacíos** amables ("No hay productos" + botón para crear el primero) y *loaders* animados.

### 2.6 UX y accesibilidad
- Mensajes claros en español en cada acción (éxito, error, aviso).
- Confirmación antes de acciones destructivas (eliminar, cancelar, vaciar carrito).
- Botones se deshabilitan mientras se guarda (evita doble envío / doble compra).
- Diseño **responsive**: 2 cortes (960 px y 720 px) para tablet y celular.
- Contraste alto (negro sobre marfil), foco visible dorado en los campos, `aria-label` en botones de ícono.
- Estilos de impresión: el comprobante y los reportes se imprimen limpios (sin menús).

## 3. Comandos

| Comando | Para qué |
|---|---|
| `npm install` | Descargar dependencias (carpeta `node_modules`) |
| `npm run dev` | Servidor de desarrollo en http://localhost:5173 (recarga al guardar) |
| `npm run build` | Compilar para producción en `dist/` (lo que hace Vercel) |
| `npm run preview` | Probar localmente la versión compilada |

En desarrollo, `vite.config.js` redirige `/api` y `/media` a `http://127.0.0.1:8000`, por eso no hay problemas de CORS en local.
