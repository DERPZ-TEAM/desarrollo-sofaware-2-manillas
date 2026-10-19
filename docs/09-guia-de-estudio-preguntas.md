# 09 · Guía de estudio para la sustentación

Preguntas que probablemente haga el profesor, con respuestas cortas y **dónde está en el código**. Recomendación: que cada integrante pueda responder TODAS, no solo "su parte".

**Reparto sugerido para presentar** (cada uno explica una parte, pero todos estudian todo):

| Integrante | Tema principal |
|---|---|
| 1 | Arquitectura, despliegue (Render/Vercel/Supabase), variables de entorno, CORS |
| 2 | Base de datos: modelos, PK/FK, migraciones, pgAdmin, esquema SQL |
| 3 | Backend: autenticación JWT, permisos, servicios (checkout, descuentos, estados) |
| 4 | Frontend: React, rutas, AuthContext, diseño UI/UX, demo en vivo |

---

## A. Arquitectura general

**1. ¿Cuál es la arquitectura del sistema?**
Tres capas desacopladas: frontend React (Vercel) → API REST Django (Render) → PostgreSQL (Supabase). Las imágenes van a Supabase Storage. Es un *monolito modular*: un solo backend dividido en módulos (`views/auth.py`, `catalogo.py`, `tienda.py`, `admin.py`).

**2. ¿Por qué REST y no GraphQL?**
Más simple, estándar, fácil de probar en el navegador, y DRF genera el CRUD con ViewSets. Nuestras pantallas no necesitan consultas complejas anidadas que justifiquen GraphQL.

**3. ¿Qué pasa, paso a paso, cuando un cliente pulsa "Añadir"?**
`ProductCard` → `useAddToCart.add()` → `api('/carrito/', POST)` agrega `Authorization: Bearer` → Django: CORS ✔ → JWT ✔ → permiso `EsCliente` ✔ → `AgregarAlCarritoSerializer` valida → `services.agregar_al_carrito` revisa stock → guarda `ItemCarrito` → responde el carrito en JSON → React actualiza el contador.

**4. ¿Por qué se separó el código en `views`, `serializers`, `services`, `models`?**
Separación de responsabilidades: la vista atiende HTTP, el serializer valida, el servicio aplica reglas de negocio y el modelo representa los datos. Así cada parte se entiende, se prueba y se cambia sin romper las demás.

## B. Base de datos

**5. ¿Qué es una llave primaria y una foránea? Den un ejemplo.**
PK: identifica cada fila (`producto.id`). FK: columna que apunta a la PK de otra tabla (`producto.categoria_id → account_categoria.id`). PostgreSQL impide FKs que apunten a filas inexistentes.

**6. ¿Dónde está el rol del usuario?**
En `account_perfil.rol` (`cliente`/`admin`), relación 1:1 con `auth_user` (FK `usuario_id` con UNIQUE). `signals.py` lo crea automáticamente y lo sincroniza con `is_staff`.

**7. ¿Qué pasa si se elimina una categoría? ¿Y un producto que ya se vendió?**
Categoría: `SET NULL`, los productos quedan sin categoría. Producto vendido: `item_pedido.producto_id` pasa a NULL pero el pedido conserva `nombre` y `precio` copiados, así el historial de ventas no cambia.

**8. ¿Por qué no se puede borrar un cliente con pedidos?**
`Pedido.usuario` tiene `on_delete=PROTECT`: las ventas son registros contables. La API responde 409 Conflict.

**9. ¿Qué es una migración? ¿Cómo agregaron los campos nuevos sin perder datos?**
Archivo que describe un cambio de estructura. La `0006` solo **agrega** columnas con valores por defecto y copia `total → subtotal` en pedidos antiguos. `migrate` la aplica una sola vez (queda registrada en `django_migrations`).

**10. ¿Por qué `DecimalField` para el precio y no `float`?**
`float` tiene errores de redondeo binario (0.1 + 0.2 ≠ 0.3). Para dinero se usa `NUMERIC` (exacto).

**11. ¿Cómo se conectan a la base de producción con pgAdmin sin dañarla?**
Session pooler de Supabase, SSL `require`, primero un backup, solo `SELECT` o transacciones con `BEGIN/ROLLBACK`, nunca cambiar estructura a mano. Ver doc 02 sección 5.

## C. Seguridad y autenticación

**12. ¿Cómo funciona el login?**
`POST /api/auth/login/` → Django compara el hash de la contraseña → devuelve `access` (30 min) y `refresh` (1 día). El frontend guarda los tokens y envía el access en cada petición.

**13. ¿Qué es un JWT y por qué no se puede falsificar?**
Texto con cabecera, contenido (user_id, rol, vencimiento) y firma hecha con `DJANGO_SECRET_KEY`. Si alguien cambia el contenido, la firma no coincide y el backend lo rechaza.

**14. ¿Cómo garantizan que un cliente no entre al panel admin?**
Dos capas: en React, `RequireAdmin` lo redirige (comodidad); en el backend, cada ruta admin tiene `@permission_classes([EsAdministrador])` que responde 403 (seguridad real). Además, el login de clientes rechaza admins y viceversa.

**15. ¿Qué pasa cuando el token vence?**
La API responde 401; `api/client.js` llama automáticamente a `/auth/refresh/`, guarda el nuevo token y repite la petición. Si el refresh también venció, se cierra la sesión con el mensaje "Tu sesión expiró".

**16. ¿Cómo es el cierre de sesión seguro?**
El refresh token se agrega a la lista negra (`token_blacklist`), y hay cierre automático tras 30 minutos de inactividad.

**17. ¿Las contraseñas se guardan en la base de datos?**
No. Se guarda un hash PBKDF2 con sal. Ni el administrador puede verlas. Por eso existe "recuperar contraseña" y no "ver contraseña".

**18. ¿Qué es CORS y cómo lo configuraron?**
Regla del navegador que impide a una página leer respuestas de otro dominio sin permiso. `django-cors-headers` con `CORS_ALLOWED_ORIGINS` (URL de Vercel) y una expresión regular para las previews. El middleware va antes de `CommonMiddleware`.

**19. ¿Qué es contenido mixto?**
Página HTTPS que pide recursos por HTTP: el navegador lo bloquea. Todas nuestras URLs son `https://`.

**20. ¿Cómo evitan inyección SQL?**
El ORM de Django usa consultas parametrizadas: los valores nunca se pegan como texto dentro del SQL.

**21. ¿Cómo evitan ataques de fuerza bruta?**
Throttling: 10 intentos de login por minuto por IP (`DEFAULT_THROTTLE_RATES`). Luego responde 429.

## D. Lógica de negocio ("lógica de programación avanzada")

**22. ¿Cómo evitan vender la misma última unidad a dos clientes?**
`crear_pedido_desde_carrito` usa `transaction.atomic` + `select_for_update()` sobre los productos (ordenados por id para evitar *deadlocks*). La segunda transacción espera y luego ve stock insuficiente. Probado en `test_checkout_falla_si_otro_compro_el_stock`.

**23. ¿Qué es una transacción atómica?**
Conjunto de operaciones que se hacen todas o ninguna. Si falla algo después de crear el pedido, PostgreSQL deshace todo (ROLLBACK).

**24. ¿Cómo calculan el descuento por mayor?**
Tabla `DESCUENTOS_POR_VOLUMEN = ((24, 15), (12, 10), (6, 5))` recorrida de mayor a menor; se aplica el primer mínimo que se cumpla. Montos con `Decimal` y redondeo `ROUND_HALF_UP`.

**25. ¿Cómo controlan los estados del pedido?**
Máquina de estados en `Pedido.TRANSICIONES` (diccionario estado → estados permitidos). `cambiar_estado_pedido` valida la transición; al cancelar devuelve el stock con `F('stock') + cantidad`. Para pasar a "enviado" se exige número de guía.

**26. ¿Qué es `F('stock')`?**
Una referencia a la columna dentro de la base de datos: la resta se hace en PostgreSQL (`SET stock = stock - 3`), evitando condiciones de carrera.

**27. ¿Cómo se hace el reporte por mes?**
`TruncMonth('creado')` + `values('periodo')` + `annotate(Sum('total'), Count('id'))` = `GROUP BY date_trunc('month', creado)`.

**28. ¿Qué es el problema N+1 y cómo lo evitan?**
Hacer 1 consulta para la lista y N más para cada relación. Lo evitamos con `select_related` (JOIN) y `prefetch_related` (una consulta extra para todos).

## E. Imágenes

**29. ¿Dónde se guardan las fotos y por qué?**
En Supabase Storage (bucket público `imagenes-productos`) mediante `account/storage.py`. Render borra su disco en cada despliegue; en el sistema original las fotos subidas se perdían y la URL apuntaba a un archivo que no existía.

**30. ¿Qué validaciones tienen las imágenes?**
Extensión JPG/PNG/WEBP, máximo 5 MB, Pillow verifica que realmente sea una imagen, nombre único con UUID y se borra la imagen anterior al reemplazarla.

## F. Frontend

**31. ¿Qué es React y qué es una SPA?**
Librería para construir interfaces con componentes. SPA: se carga una sola página y React cambia las pantallas sin recargar.

**32. ¿Qué es `useState` y `useEffect`?**
`useState` guarda datos que, al cambiar, vuelven a dibujar la pantalla. `useEffect` ejecuta código al abrir la pantalla o cuando cambia algo (ej. cargar productos cuando cambian los filtros).

**33. ¿Qué es el AuthContext?**
Un almacén global con el usuario conectado y funciones `login`, `logout`, compartido por todas las pantallas.

**34. ¿Por qué `vercel.json` tiene un *rewrite*?**
Para que al recargar `/carrito` Vercel devuelva `index.html` y React muestre la pantalla, en lugar de un 404.

**35. ¿Por qué esos colores y tipografías?**
Negro + dorado + marfil transmiten lujo (joyería); regla 60-30-10. Cormorant Garamond (serif clásica) para títulos, Outfit (moderna, legible) para textos. Ver doc 07.

## G. Despliegue

**36. ¿Qué hace `build.sh`?**
Instala dependencias, `collectstatic`, `migrate` y el seed. Si falla, Render no publica la versión rota.

**37. ¿Por qué gunicorn y no `runserver`?**
`runserver` es solo para desarrollo; gunicorn es un servidor de producción con varios *workers*.

**38. ¿Qué pasa si sube un cambio a GitHub?**
Render y Vercel detectan el push a `main` y redespliegan automáticamente (despliegue continuo).

**39. ¿Por qué la primera carga es lenta?**
El plan gratis de Render "duerme" el servicio tras 15 minutos sin uso; la primera petición lo despierta (~50 s).

## H. Calidad

**40. ¿Cómo saben que funciona?**
30 pruebas automáticas (`python manage.py test account`) que cubren registro, login, permisos, CRUD con imagen, filtros, carrito, checkout con descuento, rollback por falta de stock, estados de pedido, cancelación con devolución de stock y reportes. Además pruebas manuales del flujo completo en el navegador.

---

## Guion de demo en vivo (8–10 minutos)
1. Abrir `/api/salud/` en Render (muestra que backend y BD están vivos).
2. Portada → catálogo → filtrar "oro amarillo" y rango de precio → detalle con ficha técnica.
3. Registrar un cliente → agregar 6 piezas → mostrar descuento 5 % → checkout → comprobante.
4. Intentar abrir `/admin` con el cliente → redirige (y explicar el 403 del backend).
5. Cerrar sesión → `/admin/ingresar` → escritorio con la venta y alertas de stock.
6. Crear un producto **con foto** → verlo en la tienda.
7. Pedidos: Confirmado → Enviado (pide guía) → Entregado.
8. Reportes por mes, más vendidos, sin ventas.
9. pgAdmin: `SELECT` de pedidos con JOIN para mostrar las FK.
10. Terminal: `python manage.py test account` → OK.
