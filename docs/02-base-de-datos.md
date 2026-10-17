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

> ✅ La migración 0006 **solo agrega** columnas con valores por defecto: no borra ni modifica datos existentes. Es segura sobre la base de producción.

## 2. Modelo entidad-relación

```mermaid
erDiagram
    auth_user ||--|| account_perfil : "tiene (1:1)"
    auth_user ||--o| carrito : "tiene (1:1)"
    auth_user ||--o{ pedido : "realiza (1:N)"
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
        varchar telefono
        varchar direccion
        varchar ciudad
    }
    account_categoria {
        bigint id PK
        varchar nombre UK
        varchar slug UK
        bool activa
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
        int usuario_id FK
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
| pedido → usuario | `PROTECT` | **No se puede borrar** un cliente que tiene compras: las ventas son registros contables |
| item_pedido → pedido | `CASCADE` | El detalle pertenece al pedido |
| item_pedido → producto | `SET NULL` | Si se borra un producto, el historial de ventas se conserva (por eso guardamos `nombre` y `precio` copiados) |

**Restricciones adicionales:**
- `UNIQUE (carrito_id, producto_id)`: un producto aparece una sola vez por carrito (si lo agregas de nuevo, se suma la cantidad).
- `UNIQUE` en `usuario_id` de perfil y carrito → relación **uno a uno**.
- `CHECK (stock >= 0)`: PostgreSQL rechaza stock negativo aunque el código fallara.
- `CHECK (total >= 0)` en pedido.
- **Índices** en `precio`, `estado`, `creado`, `(activo, categoria_id)` para que filtros y reportes sean rápidos.

## 4. Usuarios y el campo `rol`

Django ya trae la tabla `auth_user` (usuario, correo, contraseña con hash). En lugar de reemplazarla, la **extendemos** con `account_perfil` (relación 1:1) que tiene el campo **`rol`** (`cliente` o `admin`), teléfono y dirección.

Para que el rol y el permiso del panel de Django siempre coincidan, `account/signals.py` sincroniza automáticamente: si `is_staff = True` → `rol = 'admin'`; si no → `'cliente'`.

> **Las contraseñas nunca se guardan en texto plano.** Django guarda algo como `pbkdf2_sha256$870000$sal$hash...`. Ni siquiera el administrador puede ver la contraseña original.

El esquema SQL completo y comentado está en [`esquema.sql`](esquema.sql).

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
