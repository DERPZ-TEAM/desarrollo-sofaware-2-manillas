# 02 · Base de datos (PostgreSQL), llaves y pgAdmin

## 1. ¿Quién crea las tablas?

No escribimos `CREATE TABLE` a mano. Django lo hace a partir de `proyecto/account/models.py`:

1. Escribimos/cambiamos una clase en `models.py`.
2. `python manage.py makemigrations` → Django genera un archivo en `account/migrations/` describiendo el cambio.
3. `python manage.py migrate` → Django ejecuta el SQL en PostgreSQL y anota la migración en la tabla `django_migrations` para no repetirla.

Migraciones del proyecto:

| Archivo | Qué hizo |
|---|---|
| `0001_initial` | Tabla de productos |
| `0002_carrito_itemcarrito` | Carrito e ítems del carrito |
| `0003_categoria_producto_categoria` | Categorías y FK producto→categoría |
| `0004_...` | Pedidos, ítems de pedido, perfil (rol) |
| `0005_...` | Renombró tablas de perfil y categoría |
| `0006_campos_ficha_envio_reportes` | **Nueva (sprints 2-5):** ficha técnica (tipo de oro, quilates, peso, talla, elaboración), stock mínimo, datos de envío y pago, guía, descuento, dirección del perfil, índices y CHECK. Incluye un paso de datos que copia `total → subtotal` en pedidos antiguos |
| `0007_reiniciar_contadores_id` | Pone los contadores automáticos de `id` en el valor más alto existente (los datos importados con JSON los habían dejado atrás y no se podían crear carritos ni pedidos) |
| `0008_catalogo_demo` | Carga 29 piezas de demostración en 7 categorías con su imagen (`account/datos_demo/catalogo/`). Solo corre una vez y no toca productos existentes |
| `0009_cliente_y_papelera` | Crea la tabla **`cliente`**, agrega `eliminado_en` (Papelera) a producto y categoría, agrega `pedido.cliente_id` (aún opcional) y renombra `pedido.usuario_id` → `registrado_por_id` |
| `0010_datos_clientes` | **Paso de datos:** por cada usuario cliente (o que tenga pedidos) crea su fila en `cliente` copiando nombre, correo, teléfono y dirección del perfil, y enlaza sus pedidos. Los administradores no se vuelven clientes |
| `0011_cliente_obligatorio` | `pedido.cliente_id` pasa a obligatorio (`PROTECT`) y se quitan del perfil los datos personales que ya se copiaron a `cliente` |
| `0012_cliente_solo_si_compra` | **Regla nueva: cliente = el que compró.** Quita las fichas de cliente de las cuentas que nunca hicieron un pedido (siguen siendo usuarios). No toca clientes con pedidos, clientes del local ni lo que está en la Papelera |

> ¿Por qué tres migraciones y no una? PostgreSQL no deja cambiar la estructura de una tabla en la misma transacción en la que se acaban de modificar sus filas ("pending trigger events"). Por eso se separa: **crear columnas → copiar datos → volver obligatoria la columna**.

> ✅ La migración 0006 **solo agrega** columnas con valores por defecto: no borra ni modifica datos existentes. Es segura sobre la base de producción.

## 2. Modelo entidad-relación

```mermaid
erDiagram
    auth_user ||--|| account_perfil : "tiene (1:1)"
    auth_user |o--o| cliente : "puede ser (1:0..1)"
    auth_user ||--o| carrito : "tiene (1:1)"
    cliente ||--o{ pedido : "compra (1:N)"
    auth_user |o--o{ pedido : "registra (1:N)"
    account_categoria ||--o{ producto : "agrupa (1:N)"
    carrito ||--o{ item_carrito : "contiene (1:N)"
    producto ||--o{ item_carrito : "aparece en"
    pedido ||--|{ item_pedido : "contiene (1:N)"
    producto ||--o{ item_pedido : "se vendió en"

    auth_user {
        int id PK
        varchar username UK
        varchar email
        varchar password "hash"
        bool is_staff
    }
    account_perfil {
        bigint id PK
        int usuario_id FK,UK
        varchar rol "cliente | admin"
    }
    cliente {
        bigint id PK
        int usuario_id FK,UK "nullable"
        varchar tipo_documento "CC|CE|TI|PAS"
        varchar numero_documento "UK con tipo"
        varchar nombres
        varchar apellidos
        varchar correo
        varchar telefono
        varchar direccion
        varchar ciudad
        timestamptz eliminado_en "Papelera"
    }
    account_categoria {
        bigint id PK
        varchar nombre UK
        varchar slug UK
        bool activa
        timestamptz eliminado_en "Papelera"
    }
    producto {
        bigint id PK
        bigint categoria_id FK
        varchar nombre
        numeric precio
        int stock
        int stock_minimo
        varchar imagen
        bool activo
        varchar tipo_oro
        smallint quilates
        numeric peso_gramos
        numeric talla_cm
        varchar elaboracion
        timestamptz eliminado_en "Papelera"
    }
    carrito {
        bigint id PK
        int usuario_id FK,UK
    }
    item_carrito {
        bigint id PK
        bigint carrito_id FK
        bigint producto_id FK
        int cantidad
    }
    pedido {
        bigint id PK
        bigint cliente_id FK
        int registrado_por_id FK "nullable"
        numeric subtotal
        numeric descuento
        numeric total
        varchar estado
        varchar metodo_pago
        varchar direccion_envio
        varchar numero_guia
    }
    item_pedido {
        bigint id PK
        bigint pedido_id FK
        bigint producto_id FK "nullable"
        varchar nombre
        numeric precio
        int cantidad
    }
```

## 3. Llaves primarias y foráneas explicadas

**Llave primaria (PK):** cada tabla tiene una columna `id` que Django crea con `BigAutoField` (en PostgreSQL: `BIGSERIAL`). Es un número que se autoincrementa y nunca se repite. Sirve para encontrar una fila exacta: `/api/productos/7/` busca `WHERE id = 7`.

**Llave foránea (FK):** guarda el `id` de otra tabla para relacionarlas. PostgreSQL **garantiza** que ese id exista (integridad referencial): no puedes crear un ítem de pedido apuntando a un pedido que no existe.

**¿Qué pasa al borrar?** (`on_delete`) — es una decisión de diseño importante:

| Relación | Regla | ¿Por qué? |
|---|---|---|
| perfil → usuario | `CASCADE` | Si se borra el usuario, su perfil ya no tiene sentido |
| carrito → usuario | `CASCADE` | Igual que arriba |
| item_carrito → producto | `CASCADE` | Si se borra un producto, desaparece de los carritos |
| producto → categoría | `SET NULL` | Si se borra la categoría, el producto **no se pierde**, queda "sin categoría" |
| cliente → usuario | `SET NULL` | Si se borra la cuenta web, la persona (cliente) y sus compras se conservan |
| pedido → cliente | `PROTECT` | **No se puede borrar** un cliente que tiene compras: las ventas son registros contables |
| pedido → registrado_por (usuario) | `SET NULL` | Si se borra la cuenta que registró la venta, la venta sigue |
| item_pedido → pedido | `CASCADE` | El detalle pertenece al pedido |
| item_pedido → producto | `SET NULL` | Si se borra un producto, el historial de ventas se conserva (por eso guardamos `nombre` y `precio` copiados) |

**Restricciones adicionales:**
- `UNIQUE (carrito_id, producto_id)`: un producto aparece una sola vez por carrito (si lo agregas de nuevo, se suma la cantidad).
- `UNIQUE` en `usuario_id` de perfil y carrito → relación **uno a uno**.
- `UNIQUE` en `cliente.usuario_id` (que además admite NULL) → relación **uno a cero-o-uno**.
- `UNIQUE (tipo_documento, numero_documento)` **parcial** (`WHERE numero_documento <> ''`): no se repite un documento, pero se permiten varios clientes antiguos que aún no lo han dado.
- `CHECK (stock >= 0)`: PostgreSQL rechaza stock negativo aunque el código fallara.
- `CHECK (total >= 0)` en pedido.
- **Índices** en `precio`, `estado`, `creado`, `(activo, categoria_id)` para que filtros y reportes sean rápidos.

## 4. Usuario ≠ Cliente, y el campo `rol`

| | **Usuario** (`auth_user` + `account_perfil`) | **Cliente** (`cliente`) |
|---|---|---|
| ¿Qué es? | Una **cuenta** para entrar al sistema (usuario + contraseña) | Una **persona** que compra |
| Ejemplos | El administrador, un cliente que se registró en la web | Un cliente de la web **o** alguien que compró en el local sin cuenta |
| Datos | username, correo, contraseña (hash), `rol` | documento, nombres, teléfono, dirección |

- Un administrador es usuario pero **no** es cliente.
- **Se es cliente solo al comprar.** Registrarse en la web crea únicamente el usuario. La ficha de cliente nace en la **primera compra**: el checkout pide el documento y guarda teléfono y dirección. Si la compra falla, la ficha tampoco se crea (va dentro de la misma transacción).
- Una persona que compra en el local es cliente pero **no** tiene usuario (`usuario_id = NULL`). La registra el administrador en *Clientes → Registrar cliente*.
- Si esa persona luego compra en la web con el **mismo documento**, se le enlaza su cliente existente (no se duplica y conserva su historial). Si el documento ya es de otra cuenta, la compra se rechaza.
- En el panel hay dos pantallas: **Usuarios** (todas las cuentas, con "¿Es cliente?") y **Clientes** (solo los que compraron).

| Persona | ¿Usuario? | ¿Cliente? |
|---|---|---|
| Se registró en la web y no ha comprado | Sí | No |
| Se registró y compró | Sí | Sí (desde su primera compra) |
| Compró en el local, sin cuenta | No | Sí |
| El del local que luego compra en la web | Sí | Sí (la misma ficha) |
| Administrador | Sí | No |
- El pedido guarda las dos cosas: `cliente_id` (quién compra) y `registrado_por_id` (qué cuenta lo registró).

`account_perfil` (1:1 con `auth_user`) guarda solo el **`rol`** de la cuenta (`cliente` o `admin`).

Para que el rol y el permiso del panel de Django siempre coincidan, `account/signals.py` sincroniza automáticamente: si `is_staff = True` → `rol = 'admin'`; si no → `'cliente'`.

> **Las contraseñas nunca se guardan en texto plano.** Django guarda algo como `pbkdf2_sha256$870000$sal$hash...`. Ni siquiera el administrador puede ver la contraseña original.

El esquema SQL completo y comentado está en [`esquema.sql`](esquema.sql).

## 4.1 Borrado lógico y Papelera

Cuando el administrador pulsa **Eliminar** en Productos, Categorías o Clientes, la fila **no se borra**: se llena la columna `eliminado_en` con la fecha y hora (**borrado lógico**). Así:

- Deja de verse en la tienda y en las listas del panel (el *manager* `objects` de Django filtra `eliminado_en IS NULL`; `todos` ve también lo eliminado).
- Aparece en **Admin → Papelera**, donde se puede **Restaurar** (vuelve `eliminado_en = NULL`) o **Eliminar definitivamente** (`DELETE` real = **borrado físico**).
- Un producto en la papelera se quita de los carritos; un cliente en la papelera deja su cuenta web desactivada (`is_active = false`) hasta restaurarlo.
- **No se puede eliminar definitivamente** un cliente con pedidos (son registros contables: `PROTECT`). Un producto sí: el historial de ventas se conserva porque `item_pedido` guarda nombre y precio copiados.
- No se pueden crear dos categorías con el mismo nombre aunque una esté en la papelera: el sistema pide restaurarla.

## 5. Conectar pgAdmin a la base de producción SIN perder datos

La base de datos de producción vive en **Supabase** (PostgreSQL en la nube). pgAdmin es solo una "ventana" para mirarla: conectarse **no modifica nada**. El riesgo está en ejecutar comandos que escriban (`UPDATE`, `DELETE`, `DROP`). Sigue estas reglas:

### 5.1 Obtener los datos de conexión

**Si usan Supabase (recomendado, es lo que ya tienen):**
1. Entrar a https://supabase.com → proyecto → botón **Connect** (arriba).
2. Pestaña **Connection string** → elegir **Session pooler** (funciona con IPv4; la conexión "Direct" es solo IPv6 y Render y muchas redes no la soportan).
3. Verás algo como: `postgresql://postgres.abcdxyz:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

**Si usan Render PostgreSQL:**
1. Render → la base de datos → **Connections** → copiar **External Database URL**.
2. Render solo permite conexiones externas desde IPs autorizadas: en **Access Control** agrega tu IP (o `0.0.0.0/0` temporalmente y luego quítala).

### 5.2 Registrar el servidor en pgAdmin
1. pgAdmin → clic derecho en *Servers* → **Register → Server…**
2. Pestaña **General** → Name: `GoldBracelets PRODUCCIÓN` (ponle "PRODUCCIÓN" para no confundirte).
3. Pestaña **Connection** (copiar de la URL `postgresql://USUARIO:CLAVE@HOST:PUERTO/BD`):
   - Host: `aws-0-us-east-1.pooler.supabase.com`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres.abcdxyz`
   - Password: la de la base (marca *Save password* solo en tu equipo personal)
4. Pestaña **Parameters** (o *SSL* en versiones viejas) → **SSL mode = require**. Sin SSL la conexión se rechaza y, además, la contraseña viajaría sin cifrar.
5. **Save**. Las tablas están en `Databases → postgres → Schemas → public → Tables`.

### 5.3 Reglas de oro para no perder datos
1. **Primero un respaldo** (ver 5.4) antes de cualquier cambio manual.
2. **Nunca** cambies la estructura (columnas/tablas) desde pgAdmin: hazlo con modelos + migraciones, o Django y la BD quedarán desincronizados.
3. Para consultar usa solo `SELECT`. Si necesitas modificar algo, usa una transacción para poder deshacer:
   ```sql
   BEGIN;
   UPDATE producto SET stock = 10 WHERE id = 3;
   SELECT id, nombre, stock FROM producto WHERE id = 3;  -- revisar
   COMMIT;   -- o ROLLBACK; si algo salió mal
   ```
4. Ideal: crear un usuario de solo lectura para revisar datos:
   ```sql
   CREATE ROLE lector LOGIN PASSWORD 'una-clave-larga';
   GRANT CONNECT ON DATABASE postgres TO lector;
   GRANT USAGE ON SCHEMA public TO lector;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO lector;
   ```
5. Nunca compartas la contraseña por el chat del grupo ni la subas a GitHub.

### 5.4 Hacer y restaurar respaldos
- **Desde pgAdmin:** clic derecho en la base → **Backup…** → Format *Custom* → archivo `goldbracelets_AAAA-MM-DD.backup`.
- **Restaurar** (por ejemplo en tu PostgreSQL local para practicar sin miedo): crea una base vacía `goldbracelets` → clic derecho → **Restore…** → elige el archivo.
- **Supabase** además guarda respaldos diarios automáticos (Database → Backups).
- **Con Django** (respaldo lógico de los datos): `python manage.py dumpdata account auth.user --indent 2 > respaldo.json` y para cargar: `python manage.py loaddata respaldo.json`.

### 5.5 Base de datos local para desarrollo
Cada integrante debe trabajar con **su propio PostgreSQL local** y no con producción:
1. pgAdmin → *Servers → PostgreSQL 18 → Databases* → clic derecho → **Create → Database** → nombre `goldbracelets`.
2. Copiar `proyecto/.env.example` a `proyecto/.env` y poner su `DB_PASSWORD`.
3. `python manage.py migrate` y `python manage.py seed_goldbracelets`.

## 6. Consultas útiles para la sustentación
Están al final de [`esquema.sql`](esquema.sql): usuarios con rol (JOIN por FK), productos con categoría, bajo stock, ventas por mes y más vendidos.
