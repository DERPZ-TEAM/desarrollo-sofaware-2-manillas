# 04 · Backend explicado archivo por archivo

Carpeta: `proyecto/`. Es un proyecto **Django** con una sola aplicación propia llamada `account` (se llama así por razones históricas: así se creó en el sprint 1 y renombrarla obligaría a recrear las tablas de producción).

```
proyecto/
├── manage.py                  # "control remoto" de Django: runserver, migrate, test...
├── requirements.txt           # librerías de Python que instala Render
├── build.sh                   # pasos que Render ejecuta en cada despliegue
├── .env.example               # plantilla de variables para desarrollo local
├── proyecto/                  # CONFIGURACIÓN del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py                # punto de entrada que usa gunicorn en Render
└── account/                   # NUESTRA APLICACIÓN
    ├── apps.py                # registra la app y carga signals.py al iniciar
    ├── models.py              # tablas
    ├── serializers.py         # validación + JSON
    ├── services.py            # reglas del negocio
    ├── permissions.py         # admin / cliente
    ├── exceptions.py          # errores globales
    ├── storage.py             # imágenes en Supabase
    ├── signals.py             # crea el Perfil automáticamente
    ├── admin.py               # panel /django-admin/
    ├── urls.py                # rutas /api/...
    ├── views/                 # vistas separadas por módulo
    │   ├── __init__.py        # /api/salud/
    │   ├── auth.py            # registro, login, perfil, contraseñas
    │   ├── catalogo.py        # productos y categorías
    │   ├── tienda.py          # carrito, checkout, mis pedidos
    │   └── admin.py           # dashboard, pedidos, clientes, inventario, reportes
    ├── management/commands/seed_goldbracelets.py   # datos iniciales
    ├── migrations/            # historial de cambios de la BD
    ├── static/images/         # fotos de ejemplo para el seed
    └── tests/test_api.py      # 30 pruebas automáticas
```

---

## 1. `proyecto/settings.py` — configuración

Organizado en 11 secciones numeradas con comentarios. Lo más importante:

| Sección | Qué configura | Detalle clave |
|---|---|---|
| 1. `.env` | Lee `proyecto/.env` en local | Función `cargar_archivo_env`: usa `setdefault`, así las variables reales de Render tienen prioridad |
| 2. Seguridad | `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` | Si `DEBUG=False` y no hay `DJANGO_SECRET_KEY`, el servidor **no arranca** (falla seguro) |
| 3. Apps y middleware | Qué módulos usa Django | `corsheaders` antes de `CommonMiddleware`; `whitenoise` para estáticos |
| 4. Base de datos | PostgreSQL | Si existe `DATABASE_URL` la usa (producción); si no, `DB_NAME/DB_USER/...` (local). Función `base_de_datos_desde_url` convierte la URL en el diccionario de Django y agrega `sslmode=require` para hosts remotos |
| 5. Contraseñas/idioma | Validadores, `es-co`, `America/Bogota` | — |
| 6. Archivos | Estáticos e imágenes | Si hay `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` → `SupabaseStorage`; si no, disco local (`media/`) |
| 7. CORS | Orígenes permitidos | Ver doc 03 |
| 8. DRF + JWT | Autenticación, permisos por defecto, manejador de errores, límites | Por defecto **todo exige login**; lo público se abre explícitamente con `AllowAny` |
| 9. Correo | SMTP o consola | Sin `EMAIL_HOST`, los correos se imprimen en el log |
| 10. HTTPS | Solo con `DEBUG=False` | Redirección a HTTPS, HSTS, cookies seguras |
| 11. Logs | Formato de los mensajes | Se ven en Render → Logs |

## 2. `proyecto/urls.py` — rutas principales

```python
urlpatterns = [
    path('', inicio),                          # JSON: "GoldBracelets API funcionando"
    path('django-admin/', admin.site.urls),    # panel interno de Django
    path('api/', include('account.urls')),     # toda nuestra API
]
```

## 3. `account/models.py` — las tablas

Cada clase = una tabla; cada atributo = una columna. Ver el diagrama en [02-base-de-datos.md](02-base-de-datos.md).

Puntos para explicar:

- **`generar_slug_unico`**: crea textos tipo `pulsera-tejida-imperial` para URLs; si ya existe, agrega `-2`, `-3`… (bucle `while`).
- **`ruta_imagen_producto`**: renombra cada imagen subida a `productos/<uuid>.jpg`. Un UUID es un identificador aleatorio de 32 caracteres, así dos fotos con el mismo nombre nunca se pisan.
- **`Producto.estado_stock`** (propiedad calculada, no es columna):
  ```python
  if self.stock == 0: return 'agotado'
  if self.stock <= self.stock_minimo: return 'bajo'
  return 'ok'
  ```
- **`Pedido.TRANSICIONES`** — una **máquina de estados**: diccionario que dice a qué estados se puede pasar desde cada estado:
  ```python
  TRANSICIONES = {
      PENDIENTE:  {CONFIRMADO, CANCELADO},
      CONFIRMADO: {ENVIADO, CANCELADO},
      ENVIADO:    {ENTREGADO},
      ENTREGADO:  set(),          # estado final
      CANCELADO:  set(),          # estado final
  }
  ```
  Así es imposible, por ejemplo, "des-cancelar" un pedido o pasar de pendiente a entregado.
- **`ItemPedido`** guarda `nombre` y `precio` copiados: si mañana el admin cambia el precio, las ventas pasadas no cambian.
- `DecimalField` para dinero (nunca `float`, que tiene errores de redondeo: `0.1 + 0.2 = 0.30000000000000004`).

## 4. `account/serializers.py` — validación y JSON

Un serializer hace dos cosas:
1. **Validar entrada**: cada método `validate_<campo>` revisa un campo; `validate()` revisa reglas entre campos.
2. **Dar formato de salida**: convierte el objeto en JSON.

| Serializer | Uso | Validaciones destacadas |
|---|---|---|
| `RegistroSerializer` | Registro | usuario solo letras/números/`._`, usuario y correo únicos (sin importar mayúsculas), nombres solo letras y se ponen en "Título", contraseñas iguales y seguras |
| `LoginSerializer` | Login | campos obligatorios |
| `ActualizarPerfilSerializer` | Mi cuenta | correo no usado por otro, teléfono 7–20 dígitos |
| `ProductoListSerializer` | Mostrar productos | agrega `imagen_url`, `categoria_nombre`, `estado_stock`, textos legibles (`tipo_oro_display`) |
| `ProductoWriteSerializer` | Crear/editar productos | nombre ≥ 3, descripción ≥ 10, precio > 0, categoría obligatoria y existente, talla 10–30 cm, **imagen**: extensión jpg/png/webp, tamaño ≤ 5 MB; al reemplazar la foto borra la anterior del bucket |
| `CarritoSerializer` | Ver carrito | calcula `resumen`: piezas, subtotal, % descuento, descuento y total |
| `CheckoutSerializer` | Comprar | dirección ≥ 6 caracteres, teléfono obligatorio, método de pago dentro de las opciones |
| `PedidoSerializer` | Mostrar pedidos | agrega `estados_siguientes` para que el panel solo muestre botones válidos |
| `PedidoAdminUpdateSerializer` | Admin cambia estado | para pasar a **enviado** exige número de guía |

Función `url_publica_imagen`: arma la URL pública de Supabase (`{SUPABASE_URL}/storage/v1/object/public/{bucket}/{archivo}`) o, en local, `http://127.0.0.1:8000/media/...`.

## 5. `account/services.py` — reglas del negocio ⭐

Es el archivo con la **lógica de programación más importante**.

### 5.1 Descuento por volumen (requisito 27 de la especificación)

```python
DESCUENTOS_POR_VOLUMEN = ((24, Decimal('15')), (12, Decimal('10')), (6, Decimal('5')))

def porcentaje_descuento(cantidad_total):
    for minimo, porcentaje in DESCUENTOS_POR_VOLUMEN:   # de mayor a menor
        if cantidad_total >= minimo:
            return porcentaje
    return Decimal('0')
```
Ejemplo: 6 pulseras de $100.000 → subtotal $600.000, descuento 5 % = $30.000, total $570.000. Se recorre la tabla de mayor a menor para devolver el **mejor** descuento que aplique. Cambiar las reglas es tan simple como editar la tupla.

### 5.2 Agregar al carrito
1. Producto debe existir y estar activo (si no → 404).
2. Si `stock == 0` → "agotado" (**corrige el bug original**).
3. `get_or_create` busca el ítem o lo crea; se suma la cantidad.
4. Si la suma supera el stock, se ajusta al máximo y se avisa.

### 5.3 Checkout transaccional `crear_pedido_desde_carrito`

```python
@transaction.atomic                       # TODO o NADA
def crear_pedido_desde_carrito(usuario, datos_envio):
    ...
    ids = sorted(i.producto_id for i in items)        # orden fijo → evita "deadlocks"
    productos = {p.id: p for p in Producto.objects.select_for_update()
                                         .filter(pk__in=ids).order_by('id')}
    # validar activo y stock de cada uno
    totales = calcular_totales(...)
    pedido = Pedido.objects.create(...)
    ItemPedido.objects.bulk_create([...])             # un solo INSERT para todos los ítems
    for producto, cantidad in lineas:
        Producto.objects.filter(pk=producto.pk).update(stock=F('stock') - cantidad)
    carrito.items.all().delete()
    return pedido
```

Conceptos a explicar:
- **`transaction.atomic`**: si cualquier línea falla (ej. stock insuficiente), PostgreSQL hace *ROLLBACK* y no queda un pedido a medias ni stock descontado. (Hay una prueba automática que lo verifica.)
- **`select_for_update()`**: genera `SELECT ... FOR UPDATE`, que **bloquea** esas filas hasta terminar la transacción. Si dos clientes compran la última unidad al mismo tiempo, el segundo espera y luego ve stock 0 → no se vende dos veces (problema de **concurrencia**).
- **Orden fijo por id**: si dos transacciones bloquean productos en distinto orden podrían esperarse mutuamente para siempre (*deadlock*). Ordenar evita eso.
- **`F('stock') - cantidad`**: la resta se hace dentro de PostgreSQL (`UPDATE producto SET stock = stock - 3`), no en Python, evitando leer un valor viejo.
- **`bulk_create`**: inserta todos los ítems en una sola consulta.

### 5.4 Cambiar estado de un pedido
```python
@transaction.atomic
def cambiar_estado_pedido(pedido, nuevo_estado):
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    if not pedido.puede_cambiar_a(nuevo_estado):
        raise ErrorDeNegocio('No se puede pasar un pedido de ... a ...')
    if nuevo_estado == Pedido.CANCELADO:
        # devolver al inventario lo que se descontó (HU-IN-026 inversa)
        for item in pedido.items.filter(producto__isnull=False):
            Producto.objects.filter(pk=item.producto_id).update(stock=F('stock') + item.cantidad)
    ...
```

## 6. `account/permissions.py` — quién puede qué
Ver explicación completa en [03-seguridad-autenticacion-cors.md](03-seguridad-autenticacion-cors.md#3-cómo-el-backend-decide-si-eres-admin-o-cliente).

## 7. `account/exceptions.py` — manejo global de errores
- `ErrorDeNegocio(mensaje, codigo)`: excepción propia para reglas del negocio. `services.py` la lanza y el manejador la convierte en `{"detail": mensaje}` con código 400/404.
- `ProtectedError` (borrar un usuario con pedidos) → 409.
- `ValidationError` → 400 con `detail` (primer mensaje) + `errors` (todos por campo).
- `DatabaseError` (BD caída) → 503 y se registra en el log.
- Cualquier otro error → 500 con mensaje genérico (no se filtran detalles internos) y el detalle completo va al log.

## 8. `account/storage.py` — imágenes en Supabase
Clase `SupabaseStorage` que hereda de `Storage` de Django. Django la llama solo cuando un `ImageField` se guarda:
- `_save` → `POST {SUPABASE_URL}/storage/v1/object/{bucket}/{archivo}` con la *service key* en la cabecera `Authorization`.
- `delete` → `DELETE` del archivo (al reemplazar o eliminar productos).
- `url` → URL pública.
Usa `urllib` (librería estándar de Python): no requiere instalar nada extra.

## 9. `account/signals.py` — perfil automático
`post_save` de `User`: cada vez que se guarda un usuario, se asegura de que exista su `Perfil` y de que `rol` coincida con `is_staff`.

## 10. `account/views/` — las vistas

| Archivo | Vistas | Historias |
|---|---|---|
| `auth.py` | `registro_view`, `login_view`, `admin_login_view`, `logout_view`, `me_view`, `cambiar_password_view`, `solicitar_recuperacion_view`, `confirmar_recuperacion_view` | HU-US-001, 003, 004, HU-AU-002, HU-SE-032 |
| `catalogo.py` | `CategoriaViewSet`, `ProductoViewSet` (+ acciones `visibilidad`, `destacados`, `opciones`) | HU-IN-006…010, HU-VE-011…015, HU-IN-049 |
| `tienda.py` | `carrito_view`, `item_carrito_view`, `checkout_view`, `mis_pedidos_view`, `mi_pedido_detalle_view`, `cancelar_mi_pedido_view` | HU-CO-016…018, HU-VE-019…022, HU-PE-023 |
| `admin.py` | `dashboard_view`, `PedidoAdminViewSet`, `clientes_admin_view`, `inventario_view`, `reporte_ingresos_view`, `reporte_mas_vendidos_view`, `reporte_sin_ventas_view` | HU-US-005, HU-PE-024, 025, 050, HU-IN-028, 029, 048, HU-RE-030, 031, 045, 046 |

### Ejemplo: filtros del catálogo (`ProductoViewSet.get_queryset`)
Cada parámetro de la URL agrega un filtro al QuerySet (Django no consulta la BD hasta el final, construye **un solo SQL**):
```
/api/productos/?q=pulsera&precio_min=50000&precio_max=200000&tipo_oro=amarillo&orden=precio_asc
→ SELECT ... FROM producto
  WHERE activo AND (nombre ILIKE '%pulsera%' OR descripcion ILIKE '%pulsera%')
    AND precio >= 50000 AND precio <= 200000 AND tipo_oro = 'amarillo'
  ORDER BY precio ASC
```
Valida: precio mínimo ≤ máximo, tipo de oro dentro de la lista.

### Ejemplo: reporte de ingresos (agregaciones SQL)
```python
_ventas_validas().filter(creado__range=(inicio, fin))
    .annotate(periodo=TruncMonth('creado'))    # agrupa por mes
    .values('periodo')
    .annotate(ingresos=Sum('total'), pedidos=Count('id'))
```
equivale a `SELECT date_trunc('month', creado), SUM(total), COUNT(id) ... GROUP BY 1`. Con `periodo=dia|mes|anio` se elige `TruncDay`, `TruncMonth` o `TruncYear` desde un diccionario.

### Ejemplo: productos sin ventas (subconsulta)
```python
vendidos = ItemPedido.objects.filter(pedido__creado__range=(...)).values('producto_id')
Producto.objects.exclude(pk__in=vendidos)     # NOT IN (subconsulta)
```

## 11. `account/management/commands/seed_goldbracelets.py`
`python manage.py seed_goldbracelets` crea admin, cliente demo, 5 categorías y 6 productos de ejemplo **solo si no hay productos**. Se ejecuta en cada despliegue (`build.sh`) sin duplicar nada porque usa `get_or_create`.

## 12. `account/tests/test_api.py` — pruebas
`python manage.py test account` crea una BD temporal, corre 30 pruebas y la borra. Cubren: registro, login por correo, flujos separados admin/cliente, logout con lista negra, recuperación de contraseña, permisos, CRUD con imagen, validaciones, filtros, stock agotado, ajuste al stock, checkout con descuento, rollback cuando falta stock, máquina de estados, devolución de stock al cancelar, reportes y alertas.

## 13. Comandos útiles

| Comando | Para qué |
|---|---|
| `python manage.py runserver` | Arrancar el backend en http://127.0.0.1:8000 |
| `python manage.py makemigrations` | Generar migración después de cambiar `models.py` |
| `python manage.py migrate` | Aplicar migraciones a la BD |
| `python manage.py showmigrations` | Ver cuáles están aplicadas |
| `python manage.py createsuperuser` | Crear un admin manualmente |
| `python manage.py seed_goldbracelets` | Datos de ejemplo |
| `python manage.py test account` | Pruebas |
| `python manage.py shell` | Consola de Python con Django cargado |
| `python manage.py check --deploy` | Revisar configuración de seguridad para producción |
