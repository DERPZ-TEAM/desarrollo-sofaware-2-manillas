"""
REFERENCIAS de producto (SKU): el código que va en la etiqueta de cada pieza.

Formato:   TIPO - QUILATES - COLOR - PIEDRA - CONSECUTIVO

    AN-18K-BL-DI-001   Anillo, 18 quilates, oro blanco, con diamante, n.º 1
    PL-18K-AM-SO-004   Pulsera, 18 quilates, oro amarillo, solo oro, n.º 4
    RL-LM-SO-002       Reloj laminado (sin quilates), solo oro, n.º 2

- La referencia identifica el TIPO de producto, no cada pieza física: las 100
  pulseras iguales comparten la misma referencia y el stock dice cuántas hay.
- Cada variación (otra talla, otro color, otra piedra) es otro producto y lleva
  otra referencia.
- Si una parte no aplica (por ejemplo, sin quilates) se omite.
- El consecutivo cuenta por prefijo: AN-18K-BL-DI-001, AN-18K-BL-DI-002...
- Una vez impresa en la etiqueta NO cambia sola, aunque se edite el producto.

Este módulo no depende de la base de datos para poder usarlo también dentro de
las migraciones.
"""
import re

# valor guardado, texto visible, código en la referencia
TIPOS_PIEZA = (
    ('pulsera', 'Pulsera / manilla', 'PL'),
    ('brazalete', 'Brazalete', 'BR'),
    ('cadena', 'Cadena / collar', 'CD'),
    ('arete', 'Aretes', 'AR'),
    ('anillo', 'Anillo', 'AN'),
    ('reloj', 'Reloj', 'RL'),
    ('dije', 'Dije', 'DJ'),
    ('otro', 'Otra pieza', 'OT'),
)
PIEDRAS = (
    ('', 'Sin piedra (solo oro)', 'SO'),
    ('diamante', 'Diamante', 'DI'),
    ('esmeralda', 'Esmeralda', 'ES'),
    ('rubi', 'Rubí', 'RU'),
    ('zafiro', 'Zafiro', 'ZA'),
    ('circonia', 'Circonia', 'CZ'),
    ('cuarzo', 'Cuarzo', 'CU'),
    ('perla', 'Perla', 'PE'),
    ('otra', 'Otra piedra', 'OT'),
)
COLORES = {'amarillo': 'AM', 'blanco': 'BL', 'rosa': 'RS', 'laminado': 'LM', 'golfi': 'GF'}

TIPOS_PIEZA_CHOICES = tuple((valor, texto) for valor, texto, _ in TIPOS_PIEZA)
PIEDRAS_CHOICES = tuple((valor, texto) for valor, texto, _ in PIEDRAS)
_CODIGO_TIPO = {valor: codigo for valor, _, codigo in TIPOS_PIEZA}
_CODIGO_PIEDRA = {valor: codigo for valor, _, codigo in PIEDRAS}

PATRON = re.compile(r'^[A-Z0-9]+(-[A-Z0-9]+)*$')
LARGO_MAXIMO = 40


def prefijo(tipo_pieza, quilates, tipo_oro, piedra):
    """Todo menos el consecutivo, ej. 'AN-18K-BL-DI'."""
    partes = [_CODIGO_TIPO.get(tipo_pieza or 'otro', 'OT')]
    if quilates:
        partes.append(f'{int(quilates)}K')
    if tipo_oro in COLORES:
        partes.append(COLORES[tipo_oro])
    partes.append(_CODIGO_PIEDRA.get(piedra or '', 'OT'))
    return '-'.join(partes)


def siguiente(prefijo_ref, existentes):
    """El siguiente consecutivo libre para ese prefijo.

    existentes = referencias ya usadas que empiezan por ese prefijo.
    """
    mayor = 0
    inicio = prefijo_ref + '-'
    for ref in existentes:
        cola = ref[len(inicio):] if ref.startswith(inicio) else ''
        if cola.isdigit():
            mayor = max(mayor, int(cola))
    return f'{inicio}{mayor + 1:03d}'


def normalizar(texto):
    """Lo que escribe el admin -> formato guardado: MAYÚSCULAS, guiones en vez de espacios."""
    texto = re.sub(r'[\s_/]+', '-', (texto or '').strip().upper())
    return re.sub(r'-{2,}', '-', texto).strip('-')


def es_valida(ref):
    return 3 <= len(ref) <= LARGO_MAXIMO and bool(PATRON.match(ref))


# ---------------------------------------------------------------------------
# Para los productos que ya existían: deducir tipo y piedra del texto
# ---------------------------------------------------------------------------
_PALABRAS_TIPO = (
    ('reloj', 'reloj'), ('brazalete', 'brazalete'), ('pulsera', 'pulsera'), ('manilla', 'pulsera'),
    ('arete', 'arete'), ('topo', 'arete'), ('anillo', 'anillo'), ('argolla de matrimonio', 'anillo'),
    ('cadena', 'cadena'), ('collar', 'cadena'), ('dije', 'dije'),
)
_PALABRAS_PIEDRA = (
    ('diamante', 'diamante'), ('esmeralda', 'esmeralda'), ('rubí', 'rubi'), ('rubi', 'rubi'),
    ('zafiro', 'zafiro'), ('circonia', 'circonia'), ('zirconia', 'circonia'), ('cuarzo', 'cuarzo'),
    ('perla', 'perla'),
)


def inferir_tipo(nombre_categoria, nombre):
    """Primero por la categoría ("Aretes"), luego por el nombre ("Reloj Dorado")."""
    for texto in (nombre_categoria or '', nombre or ''):
        texto = texto.lower()
        for palabra, tipo in _PALABRAS_TIPO:
            if palabra in texto:
                return tipo
    return 'otro'


def inferir_piedra(tipo, nombre, descripcion):
    """Deduce la piedra del texto, salvo donde la palabra no habla de una piedra:
    - pulseras tejidas: "esmeralda" suele ser el color del hilo;
    - relojes: "cuarzo" es el tipo de movimiento (la maquinaria), no una piedra.
    """
    if tipo in ('pulsera', 'reloj'):
        return ''
    texto = f'{nombre} {descripcion}'.lower()
    for palabra, piedra in _PALABRAS_PIEDRA:
        if palabra in texto:
            return piedra
    return ''
