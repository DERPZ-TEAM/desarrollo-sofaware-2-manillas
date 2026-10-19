# 08 · Sprints 1 a 5 — seguimiento del proyecto

Metodología: **Scrum** con sprints de 2 a 4 semanas. Cada sprint toma historias de usuario (HU) de la
*Plantilla de Historias de Usuario* y requisitos de la *Especificación inicial*. El archivo Excel diligenciado está en
`Dodumentacion/GoldBracelets_Sprints_Software2_Grupo2_COMPLETO.xlsx` (hoja *Sprint Planning* con el mismo formato
de la plantilla + columnas de implementación y evidencia, y hoja *Resumen y tareas*).

**Total: 41 historias de usuario en 5 sprints.**

| Sprint | Fechas | Tema | # HU |
|---|---|---|---|
| 1 | 08-sep-2026 → 06-oct-2026 | Gestión del catálogo (CRUD de productos y categorías) | 4 |
| 2 | 06-oct-2026 → 27-oct-2026 | Autenticación, usuarios, seguridad e imágenes | 7 |
| 3 | 27-oct-2026 → 24-nov-2026 | Catálogo para el cliente y carrito de compras | 10 |
| 4 | 24-nov-2026 → 08-dic-2026 | Proceso de compra y gestión de pedidos | 9 |
| 5 | 08-dic-2026 → 29-dic-2026 | Inventario, reportes, ficha técnica y cierre del proyecto | 11 |

---

## Sprint 1 · Gestión del catálogo (CRUD de productos y categorías)
**Fechas:** 08-sep-2026 a 06-oct-2026  
**Objetivo del sprint:** Montar la base del proyecto (Django + PostgreSQL + React) y permitir al administrador gestionar el catálogo.

| No | Id | Título | Historia de usuario | Qué se implementó | Evidencia (archivos) |
|---|---|---|---|---|---|
| 1 | HU-IN-006 | Registrar productos | Como administrador, necesito registrar productos con sus características (nombre, descripción, precio, imagen), con la finalidad de actualizar el catálogo para los clientes. | Modelo Producto, ProductoWriteSerializer (validaciones), POST /api/productos/, formulario en AdminProducts.jsx | `account/models.py · account/serializers.py · account/views/catalogo.py · pages/admin/AdminProducts.jsx` |
| 2 | HU-IN-007 | Editar productos | Como administrador, necesito editar la información de los productos, con la finalidad de mantener actualizada la información de estos. | PATCH /api/productos/{id}/ con validación de campos; modal de edición con mensajes "Información actualizada correctamente" | `account/views/catalogo.py · pages/admin/AdminProducts.jsx` |
| 3 | HU-IN-008 | Eliminar productos | Como administrador, necesito eliminar productos del catálogo, con la finalidad de mantener el catálogo a la par con el inventario. | DELETE /api/productos/{id}/ con confirmación; 404 si ya no existe; el historial de ventas se conserva (FK SET NULL) | `account/views/catalogo.py · account/models.py (ItemPedido)` |
| 4 | HU-IN-010 | Clasificar productos por categoría | Como administrador, necesito clasificar los productos del inventario por categorías, con la finalidad de organizar y facilitar la gestión de los productos. | Modelo Categoria (FK en Producto), CRUD /api/categorias/, categoría obligatoria y validada | `account/models.py · pages/admin/AdminCategories.jsx` |

**Tareas técnicas del sprint:**

- Proyecto Django + app account, PostgreSQL local con pgAdmin
- API REST con Django REST Framework
- Frontend React + Vite con panel de administración inicial

**Cómo demostrarlo:** entrar a `/admin/ingresar` → Productos → crear, editar y eliminar una pieza; Categorías → crear y asignar.

---

## Sprint 2 · Autenticación, usuarios, seguridad e imágenes
**Fechas:** 06-oct-2026 a 27-oct-2026  
**Objetivo del sprint:** Separar los flujos de cliente y administrador con JWT, completar la gestión de cuentas, subir imágenes a Supabase y dejar el despliegue Render + Vercel funcionando.

| No | Id | Título | Historia de usuario | Qué se implementó | Evidencia (archivos) |
|---|---|---|---|---|---|
| 1 | HU-US-001 | Registrar usuario | Como un usuario, necesito registrarme mediante un formulario con mis datos personales, con la finalidad de crear una cuenta en el sistema. | POST /api/auth/registro/ con RegistroSerializer (usuario y correo únicos, contraseña segura); pantalla Register.jsx con validación en vivo | `account/serializers.py · account/views/auth.py · pages/store/Register.jsx` |
| 2 | HU-AU-002 | Iniciar sesión | Como un usuario, necesito iniciar sesión con mi correo y contraseña, con la finalidad de acceder a mi cuenta. | Login JWT con usuario o correo; dos puertas: /auth/login/ (cliente) y /auth/admin/login/ (admin); límite de 10 intentos/min | `account/views/auth.py · context/AuthContext.jsx · pages/store/Login.jsx · pages/admin/AdminLogin.jsx` |
| 3 | HU-US-003 | Recuperar contraseña | Como usuario, necesito recuperar mi contraseña con el correo electrónico, con la finalidad de poder acceder a mi cuenta. | Token de un solo uso (default_token_generator), envío por correo, pantallas Recuperar/Restablecer | `account/views/auth.py · pages/store/ForgotPassword.jsx · ResetPassword.jsx` |
| 4 | HU-US-004 | Actualizar información personal | Como un usuario, necesito actualizar mi información personal, con la finalidad de evitar errores de contacto y envío a futuro. | PUT /api/auth/me/ (nombre, correo, teléfono, dirección) y cambio de contraseña | `account/serializers.py (ActualizarPerfilSerializer) · pages/store/Profile.jsx` |
| 5 | HU-US-005 | Consultar cuentas de usuarios | Como un administrador, necesito consultar las cuentas de los usuarios, con la finalidad de conocer la información de los usuarios registrados. | GET /api/admin/clientes/ en orden alfabético, búsqueda, total de pedidos y total comprado | `account/views/admin.py · pages/admin/AdminClients.jsx` |
| 6 | HU-SE-032 | Cerrar sesión de forma segura | Como un usuario, necesito cerrar sesión de manera segura, con la finalidad de proteger mi información y evitar accesos no autorizados. | Logout con lista negra del refresh token, tokens de 30 min con rotación, cierre automático por 30 min de inactividad | `account/views/auth.py · settings.py (SIMPLE_JWT) · context/AuthContext.jsx` |
| 7 | HU-IN-009 | Cargar imágenes de productos | Como un administrador, necesito cargar imágenes de los productos, con la finalidad de mostrar visualmente las características de cada producto. | Almacenamiento en Supabase Storage, validación de formato (JPG/PNG/WEBP) y tamaño (5 MB), vista previa, borrado de la imagen anterior | `account/storage.py · account/serializers.py (validate_imagen) · AdminProducts.jsx` |

**Tareas técnicas del sprint:**

- Reorganización del backend en capas (views/, serializers, services, permissions, exceptions)
- Configuración por variables de entorno y DATABASE_URL
- CORS Vercel ↔ Render, HTTPS y cabeceras de seguridad
- Despliegue: Render (build.sh, gunicorn, WhiteNoise), Vercel (vercel.json), Supabase (BD + Storage)
- Limpieza de código duplicado y plantillas antiguas

**Cómo demostrarlo:** registrar un cliente nuevo, cerrar sesión, iniciar con el correo, recuperar contraseña, intentar entrar a `/admin` con el cliente (se bloquea), subir una foto a un producto y verla en la tienda.

---

## Sprint 3 · Catálogo para el cliente y carrito de compras
**Fechas:** 27-oct-2026 a 24-nov-2026  
**Objetivo del sprint:** Que el cliente encuentre fácilmente las piezas (búsqueda y filtros), vea su ficha y arme su carrito con totales y descuentos.

| No | Id | Título | Historia de usuario | Qué se implementó | Evidencia (archivos) |
|---|---|---|---|---|---|
| 1 | HU-VE-011 | Visualizar catálogo | Como un cliente, necesito visualizar el catálogo de productos disponibles, con la finalidad de conocer los productos ofrecidos antes de realizar una compra. | Portada con destacados y colecciones, catálogo con tarjetas, mensaje de catálogo vacío y de error de conexión | `pages/store/Home.jsx · Catalog.jsx · components/ProductCard.jsx` |
| 2 | HU-VE-12 | Consultar detalle de producto | Como un cliente, necesito consultar el detalle de un producto del catálogo, con la finalidad de conocer sus características antes de realizar la compra. | GET /api/productos/{id}/; pantalla de detalle; mensaje "Producto no disponible" si no existe | `pages/store/Product.jsx` |
| 3 | HU-VE-013 | Buscar productos por nombre | Como un cliente, necesito buscar productos por nombre, con la finalidad de encontrar rápidamente el producto deseado. | Parámetro ?q= (nombre o descripción, sin distinguir mayúsculas) | `account/views/catalogo.py (get_queryset) · Catalog.jsx` |
| 4 | HU-VE-014 | Filtrar por precio | Como un cliente, necesito filtrar productos por precio, con la finalidad de encontrar productos acordes a mi presupuesto. | ?precio_min=&precio_max=; error si el mínimo es mayor que el máximo | `account/views/catalogo.py · Catalog.jsx` |
| 5 | HU-VE-015 | Filtrar por tipo de oro | Como un cliente, necesito filtrar productos por tipo de oro, con la finalidad de encontrar productos según el material deseado. | Nuevo campo tipo_oro (amarillo, blanco, rosa, laminado, golfi); ?tipo_oro= con validación | `account/models.py · migración 0006 · Catalog.jsx` |
| 6 | HU-CO-016 | Agregar productos al carrito | Como un cliente, necesito agregar productos al carrito de compras, con la finalidad de realizar una compra posteriormente. | POST /api/carrito/; bloquea productos agotados (bug corregido) y ajusta la cantidad al stock | `account/services.py (agregar_al_carrito) · utils/useAddToCart.js` |
| 7 | HU-CO-017 | Eliminar productos del carrito | Como un usuario, necesito eliminar productos del carrito de compras, con la finalidad de modificar mi pedido antes de realizar la compra. | DELETE /api/carrito/items/{id}/; 404 si ya no existe; el carrito anterior se conserva si falla la conexión | `account/views/tienda.py · pages/store/Cart.jsx` |
| 8 | HU-CO-018 | Visualizar total del carrito | Como un usuario, necesito visualizar el total de mi compra en el carrito, con la finalidad de conocer el valor total a pagar antes de confirmar el pedido. | Resumen con subtotal, descuento por volumen (5/10/15 %) y total; $0 / mensaje si está vacío | `account/services.py (calcular_totales) · CarritoSerializer · Cart.jsx` |
| 9 | HU-SE-033 | Validar datos ingresados | Como un usuario, necesito que el sistema valide los datos ingresados, con la finalidad de garantizar que la información registrada sea correcta. | Validación doble (React + serializers) con mensajes por campo; manejador global de errores | `account/exceptions.py · components/ui.jsx (Field)` |
| 10 | HU-SE-034 | Validar campos obligatorios | Como un usuario, necesito que el sistema valide campos obligatorios y formatos antes de almacenar información, con la finalidad de evitar registros incorrectos o incompletos. | Campos requeridos marcados con *, formato de correo/teléfono/nombres, restricciones CHECK en la base de datos | `account/serializers.py · docs/esquema.sql` |

**Tareas técnicas del sprint:**

- Migración 0006 (ficha técnica, envío, pagos, índices)
- Sistema de diseño de lujo (negro, dorado, marfil) y componentes reutilizables
- Hook useAddToCart y cliente HTTP con renovación automática de token

**Cómo demostrarlo:** en `/catalogo` buscar "pulsera", filtrar por precio y por oro amarillo; abrir un producto; agregar 6 unidades y ver el 5 % de descuento en el carrito; intentar agregar un producto agotado.

---

## Sprint 4 · Proceso de compra y gestión de pedidos
**Fechas:** 24-nov-2026 a 08-dic-2026  
**Objetivo del sprint:** Convertir el carrito en un pedido de forma segura (transacción), con datos de envío, método de pago, comprobante y seguimiento de estados.

| No | Id | Título | Historia de usuario | Qué se implementó | Evidencia (archivos) |
|---|---|---|---|---|---|
| 1 | HU-VE-019 | Registrar datos de envío | Como un usuario, necesito registrar los datos de envío de mi compra, con la finalidad de recibir los productos en la dirección indicada. | Checkout paso 1: destinatario, teléfono, dirección, ciudad, departamento; opción de guardarla en el perfil | `account/serializers.py (CheckoutSerializer) · pages/store/Checkout.jsx` |
| 2 | HU-VE-020 | Seleccionar método de pago | Como un usuario, necesito seleccionar un método de pago, con la finalidad de completar correctamente mi compra. | Contra entrega, transferencia, Nequi/Daviplata, tarjeta (simulado); obligatorio | `account/models.py (METODOS_PAGO) · Checkout.jsx` |
| 3 | HU-VE-021 | Confirmar compra | Como un usuario, necesito confirmar la compra realizada, con la finalidad de finalizar mi pedido. | POST /api/checkout/ con transaction.atomic y select_for_update (sin ventas dobles); rollback ante cualquier error | `account/services.py (crear_pedido_desde_carrito)` |
| 4 | HU-VE-022 | Recibir confirmación de compra | Como un usuario, necesito recibir una confirmación de compra, con la finalidad de tener constancia de mi pedido. | Comprobante con número de pedido, detalle, descuento, envío y pago; imprimible / PDF | `pages/store/OrderDetail.jsx` |
| 5 | HU-PE-023 | Consultar estado de pedidos | Como usuario, necesito consultar el estado de mis pedidos, con la finalidad de conocer el progreso de entrega. | Historial en "Mi cuenta" con insignias de estado y línea de seguimiento; cancelación si aún no fue enviado | `account/views/tienda.py · Profile.jsx · OrderDetail.jsx` |
| 6 | HU-PE-024 | Actualizar estado de pedidos | Como un administrador, necesito actualizar el estado de los pedidos, con la finalidad de mantener información actualizada. | Máquina de estados (pendiente → confirmado → enviado → entregado / cancelado); solo transiciones válidas | `account/models.py (TRANSICIONES) · services.py (cambiar_estado_pedido) · AdminOrders.jsx` |
| 7 | HU-PE-025 | Consultar historial de pedidos | Como un administrador, necesito consultar el historial de pedidos, con la finalidad de llevar control de las ventas. | GET /api/admin/pedidos/ con filtros por estado y búsqueda por #, cliente o correo | `account/views/admin.py (PedidoAdminViewSet)` |
| 8 | HU-IN-026 | Actualizar stock automáticamente | Como un usuario, necesito que el stock se actualice automáticamente, con la finalidad de mantener el inventario actualizado. | Descuento de stock con F() al comprar y devolución al cancelar | `account/services.py` |
| 9 | HU-IN-027 | Validar disponibilidad | Como un usuario, necesito que el sistema valide disponibilidad, con la finalidad de evitar compras sin stock. | Validación al agregar, al cambiar cantidad y al confirmar (con bloqueo de filas) | `account/services.py · tests/test_api.py` |

**Tareas técnicas del sprint:**

- Transacciones atómicas y bloqueo de filas (SELECT ... FOR UPDATE)
- Descuentos por volumen para mayoristas (requisito 27 de la especificación)
- Comprobante imprimible

**Cómo demostrarlo:** completar el checkout (envío + pago) → comprobante; en el panel cambiar el pedido a Confirmado → Enviado (pide guía) → Entregado; cancelar otro pedido y ver que el stock vuelve.

---

## Sprint 5 · Inventario, reportes, ficha técnica y cierre del proyecto
**Fechas:** 08-dic-2026 a 29-dic-2026  
**Objetivo del sprint:** Dar al administrador información para decidir (inventario, alertas, reportes) y completar la ficha técnica; pruebas, documentación y despliegue final.

| No | Id | Título | Historia de usuario | Qué se implementó | Evidencia (archivos) |
|---|---|---|---|---|---|
| 1 | HU-IN-028 | Consultar estado del inventario | Como un administrador, necesito consultar el estado del inventario, con la finalidad de controlar existencias. | GET /api/admin/inventario/: unidades, valor del inventario, agotados, bajo stock; ajuste rápido de stock | `account/views/admin.py · pages/admin/AdminInventory.jsx` |
| 2 | HU-IN-029 | Visualizar ventas realizadas | Como un administrador, necesito visualizar las ventas realizadas, con la finalidad de analizar el rendimiento de ventas. | Escritorio con ventas totales, ventas del mes y pedidos recientes | `account/views/admin.py (dashboard_view) · Dashboard.jsx` |
| 3 | HU-RE-030 | Reporte de ingresos por día, mes y año | Como un administrador, necesito generar reportes de ingresos por día, mes y año, con la finalidad de analizar las ventas registradas en el sistema. | Agregación SQL con TruncDay/TruncMonth/TruncYear, rango de fechas, gráfico de barras | `account/views/admin.py (reporte_ingresos_view) · AdminReports.jsx` |
| 4 | HU-RE-031 | Productos más vendidos | Como un administrador, necesito consultar los productos más vendidos, con la finalidad de identificar los productos con mayor demanda. | Ranking por unidades (excluye cancelados) | `account/views/admin.py (reporte_mas_vendidos_view)` |
| 5 | HU-RE-046 | Más vendidos según criterios | Como un administrador, necesito consultar los productos más vendidos según criterios definidos, con la finalidad de analizar las tendencias de ventas por cantidad o categoría. | Criterio cantidad o ingresos, filtro por categoría y fechas, validación de criterio | `account/views/admin.py · AdminReports.jsx` |
| 6 | HU-RE-045 | Productos sin ventas | Como un administrador, necesito identificar productos que no han tenido ventas en un período determinado, con la finalidad de analizar productos con baja demanda. | Subconsulta NOT IN sobre item_pedido; validación de rango de fechas | `account/views/admin.py (reporte_sin_ventas_view)` |
| 7 | HU-IN-048 | Alertas de stock mínimo | Como un administrador, necesito recibir alertas cuando un producto alcance el nivel mínimo de stock definido, con la finalidad de evitar desabastecimiento. | Campo stock_minimo por producto; alertas en el escritorio e inventario; la alerta desaparece al reponer | `account/models.py (estado_stock) · Dashboard.jsx` |
| 8 | HU-PE-050 | Información de envío de pedidos | Como un administrador, necesito registrar y consultar la información de envío de los pedidos, con la finalidad de controlar el estado de entrega. | Transportadora y número de guía (obligatorio para marcar "enviado"); visible para el cliente | `account/serializers.py (PedidoAdminUpdateSerializer) · AdminOrders.jsx` |
| 9 | HU-PR-035 | Ficha técnica del producto | Como un cliente, necesito generar una ficha técnica del producto, con la finalidad de consultar las características registradas del producto. | Material, quilates, peso, talla, elaboración y categoría; avisa datos no registrados | `pages/store/Product.jsx` |
| 10 | HU-PR-038 | Tipo de elaboración | Como un administrador, necesito registrar el tipo de elaboración de cada producto, con la finalidad de diferenciar productos manuales y mecánicos. | Campo elaboracion (manual / máquina) validado | `account/models.py · AdminProducts.jsx` |
| 11 | HU-IN-049 | Disponibilidad por tallas | Como un cliente, necesito consultar la disponibilidad de productos según tallas o medidas registradas, con la finalidad de encontrar productos adecuados a mis necesidades. | Campo talla_cm (16, 18, 20 cm estándar), filtro ?talla= y "solo disponibles" | `account/views/catalogo.py · Catalog.jsx` |

**Tareas técnicas del sprint:**

- 30 pruebas automáticas (python manage.py test account)
- Documentación completa en docs/ y esquema SQL
- Guía de despliegue y de estudio para la sustentación

**Cómo demostrarlo:** Inventario (alertas), Reportes (ingresos por mes, más vendidos, sin ventas), ficha técnica en el detalle; ejecutar `python manage.py test account` (30 pruebas OK).

---

## Backlog para futuras versiones

Historias de la plantilla que quedan fuera del alcance de los 5 sprints (requieren módulos de insumos, producción a
medida o preventa). Se dejan priorizadas para una siguiente versión, coherente con la "Fase 2" del documento de arquitectura:

| Id | Descripción |
|---|---|
| HU-PR-036 | Registrar servicios realizados a los productos (mantenimiento/limpieza) |
| HU-PE-037 | Pedidos de productos personalizados |
| HU-CL-039 | Medidas personalizadas del cliente |
| HU-IN-040 | Descuento automático de insumos (balines, hilo, dijes) |
| HU-PE-041 | Pedidos en preventa |
| HU-IN-042 | Ubicación física de productos (vitrina / caja fuerte) |
| HU-IN-043 | Adjuntar archivos a productos o pedidos |
| HU-IN-044 | Tiempo estimado de entrega de personalizados |
| HU-PR-047 | Observaciones / recomendaciones de cuidado |

Requisitos de la especificación inicial cubiertos además: 1–4 (CRUD de productos con tipo, peso y quilates), 6–10 (usuarios, ventas e inventario automático), 12–13 (login y consulta de ventas), 14 (comprobante), 15 (total automático), 18 (reporte de ventas), 27 (precios por volumen), 29 y 48 (alertas de bajo stock), 34 y 46 (más vendidos), 38 (tejido manual o máquina), 45 (productos sin movimiento), 49 (tallas estándar) y 50 (número de guía).
