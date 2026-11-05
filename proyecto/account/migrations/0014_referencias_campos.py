"""
Paso 1 de 3 de las REFERENCIAS de producto: crear las columnas.

- producto.tipo_pieza  (pulsera, brazalete, reloj, ...)
- producto.piedra      (diamante, esmeralda, ...; vacío = solo oro)
- producto.referencia  (por ahora puede estar vacía; el paso 2 la llena)
- item_pedido.referencia (copia en cada venta, igual que el nombre y el precio)
"""
from django.db import migrations, models

import account.referencias


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_pago_efectivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='tipo_pieza',
            field=models.CharField(choices=account.referencias.TIPOS_PIEZA_CHOICES, default='otro', max_length=12),
        ),
        migrations.AddField(
            model_name='producto',
            name='piedra',
            field=models.CharField(blank=True, choices=account.referencias.PIEDRAS_CHOICES, default='', max_length=12),
        ),
        migrations.AddField(
            model_name='producto',
            name='referencia',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='itempedido',
            name='referencia',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
    ]
