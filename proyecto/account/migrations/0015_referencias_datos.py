"""
Paso 2 de 3: dar referencia a los productos que ya existían.

Para cada producto (del más antiguo al más nuevo, incluidos los de la Papelera):
  1. deduce el tipo de pieza (por la categoría o el nombre) y la piedra
     (por el nombre y la descripción),
  2. arma la referencia TIPO-QUILATES-COLOR-PIEDRA-NNN,
  3. copia esa referencia en las ventas ya hechas de ese producto.
El administrador puede corregir después el tipo, la piedra o la referencia.
"""
from django.db import migrations

from account import referencias


def asignar_referencias(apps, schema_editor):
    Producto = apps.get_model('account', 'Producto')
    ItemPedido = apps.get_model('account', 'ItemPedido')
    usadas = set()
    for p in Producto._base_manager.select_related('categoria').order_by('id'):
        nombre_categoria = p.categoria.nombre if p.categoria_id else ''
        p.tipo_pieza = referencias.inferir_tipo(nombre_categoria, p.nombre)
        p.piedra = referencias.inferir_piedra(p.tipo_pieza, p.nombre, p.descripcion)
        inicio = referencias.prefijo(p.tipo_pieza, p.quilates, p.tipo_oro, p.piedra)
        p.referencia = referencias.siguiente(inicio, usadas)
        usadas.add(p.referencia)
        p.save(update_fields=['tipo_pieza', 'piedra', 'referencia'])
        ItemPedido._base_manager.filter(producto_id=p.id).update(referencia=p.referencia)


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_referencias_campos'),
    ]

    operations = [
        # Volver atrás no necesita deshacer nada: el paso 1 al revertirse quita las columnas.
        migrations.RunPython(asignar_referencias, migrations.RunPython.noop),
    ]
