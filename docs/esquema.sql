-- =============================================================================
-- GoldBracelets · Esquema de base de datos (PostgreSQL 15+)
-- =============================================================================
-- IMPORTANTE: este archivo es DOCUMENTACIÓN / REFERENCIA.
-- Las tablas reales las crea Django con:   python manage.py migrate
-- (a partir de proyecto/account/models.py y las migraciones 0001 ... 0006).
-- Si ejecutas este script a mano en una base vacía, obtienes la misma estructura,
-- pero Django no sabrá que las migraciones ya se aplicaron. Úsalo para estudiar
-- o para mostrarlo en pgAdmin (Herramientas -> Query Tool).
--
-- Convenciones:
--   PK  = PRIMARY KEY  (llave primaria: identifica cada fila de forma única)
--   FK  = FOREIGN KEY  (llave foránea: apunta a la PK de otra tabla)
--   BIGSERIAL = número entero grande que se autoincrementa (1, 2, 3...)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. USUARIOS
-- auth_user es la tabla estándar de Django (la crea django.contrib.auth).
-- Se muestra resumida con las columnas que usa el proyecto.
-- -----------------------------------------------------------------------------
CREATE TABLE auth_user (
    id            SERIAL PRIMARY KEY,                 -- PK
    username      VARCHAR(150) NOT NULL UNIQUE,
    email         VARCHAR(254) NOT NULL DEFAULT '',
    password      VARCHAR(128) NOT NULL,              -- HASH (pbkdf2_sha256), nunca la clave en texto
    first_name    VARCHAR(150) NOT NULL DEFAULT '',
    last_name     VARCHAR(150) NOT NULL DEFAULT '',
    is_staff      BOOLEAN NOT NULL DEFAULT FALSE,     -- puede entrar a /django-admin/
    is_superuser  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ NULL
);

-- Perfil: relación 1 a 1 con auth_user. Aquí está el campo ROL.
CREATE TABLE account_perfil (
    id            BIGSERIAL PRIMARY KEY,                                        -- PK
    usuario_id    INTEGER NOT NULL UNIQUE                                       -- FK + UNIQUE = relación 1:1
                  REFERENCES auth_user (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    rol           VARCHAR(20) NOT NULL DEFAULT 'cliente'
                  CHECK (rol IN ('cliente', 'admin')),
    telefono      VARCHAR(20)  NOT NULL DEFAULT '',
    direccion     VARCHAR(200) NOT NULL DEFAULT '',
    ciudad        VARCHAR(80)  NOT NULL DEFAULT '',
    departamento  VARCHAR(80)  NOT NULL DEFAULT '',
    creado        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX account_perfil_rol_idx ON account_perfil (rol);

-- -----------------------------------------------------------------------------
-- 2. CATÁLOGO
-- -----------------------------------------------------------------------------
CREATE TABLE account_categoria (
    id            BIGSERIAL PRIMARY KEY,                -- PK
    nombre        VARCHAR(80)  NOT NULL UNIQUE,
    slug          VARCHAR(100) NOT NULL UNIQUE,         -- texto para URL: "pulseras-tejidas"
    descripcion   TEXT NOT NULL DEFAULT '',
    activa        BOOLEAN NOT NULL DEFAULT TRUE,
    orden         INTEGER NOT NULL DEFAULT 0 CHECK (orden >= 0),
    creado        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Producto = brazalete / pieza de joyería
CREATE TABLE producto (
    id            BIGSERIAL PRIMARY KEY,                                        -- PK
    categoria_id  BIGINT NULL                                                   -- FK (opcional)
                  REFERENCES account_categoria (id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    nombre        VARCHAR(120) NOT NULL,
    slug          VARCHAR(140) NOT NULL UNIQUE,
    descripcion   TEXT NOT NULL,
    precio        NUMERIC(12, 2) NOT NULL,              -- NUMERIC: exacto, ideal para dinero
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    stock_minimo  INTEGER NOT NULL DEFAULT 3 CHECK (stock_minimo >= 0),
    imagen        VARCHAR(100) NULL,                    -- ruta: 'productos/<uuid>.jpg' (archivo en Supabase Storage)
    activo        BOOLEAN NOT NULL DEFAULT TRUE,        -- visible en la tienda
    tipo_oro      VARCHAR(20) NOT NULL DEFAULT ''
                  CHECK (tipo_oro IN ('', 'amarillo', 'blanco', 'rosa', 'laminado', 'golfi')),
    quilates      SMALLINT NULL CHECK (quilates IN (10, 14, 18, 24)),
    peso_gramos   NUMERIC(7, 2) NULL,
    talla_cm      NUMERIC(5, 1) NULL,
    elaboracion   VARCHAR(10) NOT NULL DEFAULT '' CHECK (elaboracion IN ('', 'manual', 'maquina')),
    creado        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Índices: aceleran las búsquedas más comunes del catálogo
CREATE INDEX producto_categoria_idx        ON producto (categoria_id);
CREATE INDEX producto_activo_idx           ON producto (activo);
CREATE INDEX producto_activo_categoria_idx ON producto (activo, categoria_id);
CREATE INDEX producto_precio_idx           ON producto (precio);
CREATE INDEX producto_tipo_oro_idx         ON producto (tipo_oro);

-- -----------------------------------------------------------------------------
-- 3. CARRITO
-- -----------------------------------------------------------------------------
CREATE TABLE carrito (
    id            BIGSERIAL PRIMARY KEY,                                        -- PK
    usuario_id    INTEGER NOT NULL UNIQUE                                       -- FK 1:1 (un carrito por cliente)
                  REFERENCES auth_user (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    creado        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE item_carrito (
    id            BIGSERIAL PRIMARY KEY,                                        -- PK
    carrito_id    BIGINT NOT NULL REFERENCES carrito (id)  ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,  -- FK
    producto_id   BIGINT NOT NULL REFERENCES producto (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,  -- FK
    cantidad      INTEGER NOT NULL DEFAULT 1 CHECK (cantidad >= 0),
    agregado      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uniq_item_carrito_producto UNIQUE (carrito_id, producto_id)   -- no repetir producto en un carrito
);

-- -----------------------------------------------------------------------------
-- 4. PEDIDOS (ventas)
-- -----------------------------------------------------------------------------
CREATE TABLE pedido (
    id                  BIGSERIAL PRIMARY KEY,                                  -- PK
    usuario_id          INTEGER NOT NULL                                        -- FK
                        REFERENCES auth_user (id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    subtotal            NUMERIC(14, 2) NOT NULL DEFAULT 0,
    descuento           NUMERIC(14, 2) NOT NULL DEFAULT 0,      -- descuento por volumen (5/10/15 %)
    total               NUMERIC(14, 2) NOT NULL,
    estado              VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado')),
    metodo_pago         VARCHAR(20) NOT NULL DEFAULT 'contraentrega'
                        CHECK (metodo_pago IN ('contraentrega', 'transferencia', 'nequi', 'tarjeta')),
    nombre_destinatario VARCHAR(120) NOT NULL DEFAULT '',
    telefono_contacto   VARCHAR(20)  NOT NULL DEFAULT '',
    direccion_envio     VARCHAR(200) NOT NULL DEFAULT '',
    ciudad              VARCHAR(80)  NOT NULL DEFAULT '',
    departamento        VARCHAR(80)  NOT NULL DEFAULT '',
    transportadora      VARCHAR(60)  NOT NULL DEFAULT '',
    numero_guia         VARCHAR(60)  NOT NULL DEFAULT '',
    notas               TEXT NOT NULL DEFAULT '',
    creado              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pedido_total_no_negativo CHECK (total >= 0)
);
CREATE INDEX pedido_usuario_idx ON pedido (usuario_id);
CREATE INDEX pedido_estado_idx  ON pedido (estado);
CREATE INDEX pedido_creado_idx  ON pedido (creado);

-- Detalle del pedido. Guarda nombre y precio "congelados" del momento de la compra.
CREATE TABLE item_pedido (
    id            BIGSERIAL PRIMARY KEY,                                        -- PK
    pedido_id     BIGINT NOT NULL REFERENCES pedido (id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,    -- FK
    producto_id   BIGINT NULL     REFERENCES producto (id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED, -- FK
    nombre        VARCHAR(120) NOT NULL,
    precio        NUMERIC(12, 2) NOT NULL,
    cantidad      INTEGER NOT NULL CHECK (cantidad >= 1)
);
CREATE INDEX item_pedido_pedido_idx   ON item_pedido (pedido_id);
CREATE INDEX item_pedido_producto_idx ON item_pedido (producto_id);

-- -----------------------------------------------------------------------------
-- 5. SEGURIDAD: tokens JWT (los crea la app rest_framework_simplejwt.token_blacklist)
--    token_blacklist_outstandingtoken  -> todos los refresh tokens emitidos
--    token_blacklist_blacklistedtoken  -> los invalidados al cerrar sesión
-- -----------------------------------------------------------------------------

-- =============================================================================
-- CONSULTAS ÚTILES PARA LA SUSTENTACIÓN (pgAdmin -> Query Tool)
-- =============================================================================
-- Usuarios con su rol:
--   SELECT u.id, u.username, u.email, p.rol
--   FROM auth_user u JOIN account_perfil p ON p.usuario_id = u.id ORDER BY u.username;
--
-- Productos con su categoría (JOIN por la llave foránea):
--   SELECT p.nombre, p.precio, p.stock, c.nombre AS categoria
--   FROM producto p LEFT JOIN account_categoria c ON c.id = p.categoria_id;
--
-- Productos con stock bajo:
--   SELECT nombre, stock, stock_minimo FROM producto WHERE stock <= stock_minimo;
--
-- Ventas por mes (lo mismo que hace el reporte de ingresos):
--   SELECT date_trunc('month', creado) AS mes, SUM(total) AS ingresos, COUNT(*) AS pedidos
--   FROM pedido WHERE estado <> 'cancelado' GROUP BY 1 ORDER BY 1;
--
-- Productos más vendidos:
--   SELECT nombre, SUM(cantidad) AS unidades
--   FROM item_pedido ip JOIN pedido pe ON pe.id = ip.pedido_id
--   WHERE pe.estado <> 'cancelado' GROUP BY nombre ORDER BY unidades DESC LIMIT 10;
