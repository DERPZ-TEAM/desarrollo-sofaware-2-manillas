"""
Carga el catálogo de demostración: 29 piezas en 7 categorías, cada una con
su imagen (account/datos_demo/catalogo/*.jpg).

- Las migraciones se ejecutan UNA sola vez por base de datos (Django las anota
  en django_migrations). Si el administrador luego borra o edita un producto,
  no vuelve a aparecer en el siguiente despliegue.
- No toca productos existentes: si ya hay uno con el mismo nombre, lo salta.
- Las imágenes se suben al almacenamiento configurado (Supabase en producción).
- Solo corre en PostgreSQL; en SQLite (pruebas automáticas) no hace nada.
"""
from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.db import migrations
from django.utils.text import slugify

CARPETA = Path(__file__).resolve().parent.parent / 'datos_demo' / 'catalogo'

CATEGORIAS = [
    ('Pulseras tejidas', 'Pulseras tejidas a mano con hilo y detalles en oro.'),
    ('Pulsera', 'Pulseras de balines y eslabones para uso diario.'),
    ('Brazaletes', 'Brazaletes rígidos en oro amarillo, rosa y blanco.'),
    ('Cadenas', 'Cadenas y collares con o sin dije.'),
    ('Aretes', 'Argollas, topos y aretes con piedra.'),
    ('Anillos', 'Anillos de compromiso, argollas y anillos con piedra.'),
    ('Reloj', 'Relojes con caja dorada y correa de metal o cuero.'),
]

# (imagen, nombre, categoría, precio, stock, tipo_oro, quilates, peso_g, talla_cm, elaboración, descripción)
PRODUCTOS = [
    ('tejida-imperial', 'Pulsera Tejida Imperial', 'Pulseras tejidas', '185000', 14, 'amarillo', 18, '4.20', '18', 'manual',
     'Hilo negro trenzado a mano con cinco balines y un balín central en oro 18k. Cierre corredizo ajustable.'),
    ('tejida-roja', 'Pulsera Tejida Pasión', 'Pulseras tejidas', '149000', 20, 'amarillo', 14, '3.10', '18', 'manual',
     'Trenzado rojo intenso con cuentas en oro 14k. Ideal para regalar en fechas especiales.'),
    ('tejida-beige-rosa', 'Pulsera Tejida Arena Rosa', 'Pulseras tejidas', '172000', 9, 'rosa', 14, '3.60', '16', 'manual',
     'Hilo beige con nueve cuentas en oro rosa 14k. Delicada y femenina para uso diario.'),
    ('tejida-azul', 'Pulsera Tejida Océano', 'Pulseras tejidas', '139000', 3, 'blanco', 10, '2.80', '20', 'manual',
     'Trenzado azul profundo con cuentas en oro blanco. Diseño unisex de cierre corredizo.'),
    ('tejida-verde', 'Pulsera Tejida Esmeralda', 'Pulseras tejidas', '128000', 16, 'laminado', None, '2.40', '18', 'manual',
     'Hilo verde esmeralda con tres balines laminados en oro. Resistente al agua.'),

    ('balines-oro', 'Pulsera Balines Clásica', 'Pulsera', '210000', 12, 'amarillo', 18, '5.10', '18', 'maquina',
     'Veintiséis balines pulidos en oro 18k ensartados en hilo elástico de alta resistencia.'),
    ('balines-tricolor', 'Pulsera Balines Tricolor', 'Pulsera', '265000', 7, 'amarillo', 18, '5.80', '18', 'maquina',
     'Combinación de balines en oro amarillo, rosa y blanco. La pieza más versátil de la colección.'),
    ('balines-rosa', 'Pulsera Balines Rosé', 'Pulsera', '198000', 10, 'rosa', 14, '4.70', '16', 'maquina',
     'Balines grandes en oro rosa 14k con acabado espejo.'),
    ('balines-noche', 'Pulsera Balines Golfi', 'Pulsera', '69000', 40, 'golfi', None, '1.90', '18', 'manual',
     'Balines pequeños con baño de oro golfi. Perfecta para combinar varias en la misma muñeca.'),
    ('pulsera-eslabones', 'Pulsera Eslabón Figaro', 'Pulsera', '320000', 6, 'amarillo', 18, '7.40', '20', 'maquina',
     'Eslabones ovalados estilo figaro en oro 18k con broche de langosta.'),

    ('brazalete-clasico', 'Brazalete Dorado Clásico', 'Brazaletes', '480000', 5, 'amarillo', 18, '12.50', '18', 'maquina',
     'Brazalete rígido de perfil redondo en oro 18k pulido. Un básico atemporal.'),
    ('brazalete-rosa-piedras', 'Brazalete Rosa Aurora', 'Brazaletes', '560000', 4, 'rosa', 18, '11.80', '18', 'maquina',
     'Brazalete en oro rosa 18k con cinco circonias engastadas al frente.'),
    ('brazalete-blanco', 'Brazalete Oro Blanco Luna', 'Brazaletes', '620000', 2, 'blanco', 18, '10.90', '18', 'maquina',
     'Oro blanco 18k con nueve piedras brillantes. Pieza de colección en edición limitada.'),
    ('brazalete-abierto', 'Brazalete Abierto Esferas', 'Brazaletes', '395000', 8, 'amarillo', 14, '8.20', '18', 'manual',
     'Brazalete abierto terminado en dos esferas. Se ajusta suavemente a la muñeca.'),

    ('cadena-cartier', 'Cadena Cartier Clásica', 'Cadenas', '450000', 9, 'amarillo', 18, '9.50', None, 'maquina',
     'Cadena de eslabón cartier en oro 18k, 50 cm de largo, con broche de seguridad.'),
    ('cadena-rosa-corazon', 'Collar Corazón Rosé', 'Cadenas', '365000', 11, 'rosa', 14, '6.30', None, 'maquina',
     'Cadena fina en oro rosa 14k con dije de corazón. El regalo perfecto.'),
    ('cadena-blanca', 'Cadena Fina Oro Blanco', 'Cadenas', '298000', 13, 'blanco', 14, '4.80', None, 'maquina',
     'Cadena delicada en oro blanco 14k, ideal para llevar sola o con dije.'),
    ('cadena-gruesa', 'Cadena Cubana Imperial', 'Cadenas', '1250000', 3, 'amarillo', 18, '28.00', None, 'maquina',
     'Cadena de eslabón grueso estilo cubano en oro 18k macizo. Presencia y elegancia.'),

    ('aretes-argolla', 'Argollas Doradas Medianas', 'Aretes', '235000', 15, 'amarillo', 18, '3.40', None, 'maquina',
     'Par de argollas en oro 18k de 3 cm. Cierre de bisagra cómodo para todo el día.'),
    ('aretes-gota-esmeralda', 'Aretes Gota Esmeralda', 'Aretes', '410000', 6, 'amarillo', 18, '4.10', None, 'manual',
     'Aretes colgantes en oro 18k con piedra verde en forma de gota.'),
    ('aretes-topo-rosa', 'Topos Rosé con Circonia', 'Aretes', '168000', 18, 'rosa', 14, '1.60', None, 'maquina',
     'Topos en oro rosa 14k con circonia central. Discretos y elegantes.'),
    ('aretes-argolla-blanca', 'Argollas Oro Blanco', 'Aretes', '245000', 2, 'blanco', 18, '3.20', None, 'maquina',
     'Argollas en oro blanco 18k con acabado brillante.'),

    ('anillo-solitario', 'Anillo Solitario Diamante', 'Anillos', '890000', 4, 'blanco', 18, '3.80', None, 'manual',
     'Anillo de compromiso en oro blanco 18k con piedra central talla brillante.'),
    ('anillo-rubi', 'Anillo Rubí Real', 'Anillos', '540000', 5, 'amarillo', 18, '4.20', None, 'manual',
     'Oro amarillo 18k con piedra roja tipo rubí y garras de sujeción.'),
    ('anillo-rosa', 'Anillo Cuarzo Rosa', 'Anillos', '380000', 7, 'rosa', 14, '3.50', None, 'manual',
     'Oro rosa 14k con piedra rosada facetada. Delicado y romántico.'),
    ('anillo-argolla', 'Argolla de Matrimonio Clásica', 'Anillos', '420000', 20, 'amarillo', 18, '5.00', None, 'maquina',
     'Argolla lisa de media caña en oro 18k. Se vende por unidad.'),

    ('reloj-dorado', 'Reloj Dorado Ejecutivo', 'Reloj', '780000', 5, 'laminado', None, '65.00', None, 'maquina',
     'Caja y brazalete laminados en oro, esfera marfil y movimiento de cuarzo.'),
    ('reloj-cuero', 'Reloj Clásico Correa de Cuero', 'Reloj', '520000', 8, 'laminado', None, '48.00', None, 'maquina',
     'Caja dorada con correa de cuero café genuino. Elegancia para cualquier ocasión.'),
    ('reloj-rosa', 'Reloj Rosé Esfera Negra', 'Reloj', '690000', 3, 'rosa', None, '58.00', None, 'maquina',
     'Caja y brazalete en tono oro rosa con esfera negra de alto contraste.'),
]


def slug_unico(modelo, texto):
    base = slugify(texto) or 'item'
    slug, n = base, 1
    while modelo.objects.filter(slug=slug).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug


def cargar_catalogo(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    Categoria = apps.get_model('account', 'Categoria')
    Producto = apps.get_model('account', 'Producto')

    categorias = {}
    for orden, (nombre, descripcion) in enumerate(CATEGORIAS, start=1):
        cat = Categoria.objects.filter(nombre__iexact=nombre).first()
        if cat is None:
            cat = Categoria.objects.create(
                nombre=nombre, slug=slug_unico(Categoria, nombre),
                descripcion=descripcion, activa=True, orden=orden,
            )
        elif not cat.descripcion:
            cat.descripcion = descripcion
            cat.save(update_fields=['descripcion'])
        categorias[nombre] = cat

    for img, nombre, cat, precio, stock, oro, k, peso, talla, elab, desc in PRODUCTOS:
        if Producto.objects.filter(nombre__iexact=nombre).exists():
            continue
        producto = Producto(
            nombre=nombre, slug=slug_unico(Producto, nombre), descripcion=desc,
            categoria=categorias[cat], precio=Decimal(precio), stock=stock, stock_minimo=3,
            activo=True, tipo_oro=oro, quilates=k,
            peso_gramos=Decimal(peso) if peso else None,
            talla_cm=Decimal(talla) if talla else None,
            elaboracion=elab,
        )
        ruta = CARPETA / f'{img}.jpg'
        if ruta.exists():
            with ruta.open('rb') as archivo:
                producto.imagen.save(f'{img}.jpg', File(archivo), save=False)
        producto.save()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_reiniciar_contadores_id'),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo, migrations.RunPython.noop),
    ]
