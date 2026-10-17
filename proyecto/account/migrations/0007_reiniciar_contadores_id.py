"""
Reinicia los contadores automáticos de id (secuencias de PostgreSQL).

¿Por qué? Parte de los datos de producción se cargó desde archivos JSON con
los id ya escritos (loaddata). Eso inserta filas sin avanzar el contador, así
que PostgreSQL intentaba crear, por ejemplo, el carrito con id=1 aunque ya
existía, y fallaba con "llave duplicada".

Esta migración pone cada contador en el id más alto que ya existe en su tabla.
No modifica ni borra datos y es segura de ejecutar varias veces.
"""
from django.core.management.color import no_style
from django.db import migrations

MODELOS = ('Perfil', 'Categoria', 'Producto', 'Carrito', 'ItemCarrito', 'Pedido', 'ItemPedido')


def reiniciar_contadores(apps, schema_editor):
    conexion = schema_editor.connection
    if conexion.vendor != 'postgresql':
        return  # SQLite (pruebas) no tiene este problema
    modelos = [apps.get_model('account', nombre) for nombre in MODELOS]
    # Django genera el SQL: SELECT setval(pg_get_serial_sequence('tabla','id'), MAX(id)) ...
    with conexion.cursor() as cursor:
        for sql in conexion.ops.sequence_reset_sql(no_style(), modelos):
            cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_campos_ficha_envio_reportes'),
    ]

    operations = [
        migrations.RunPython(reiniciar_contadores, migrations.RunPython.noop),
    ]
