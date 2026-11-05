"""
Paso 3 de 3: la referencia pasa a ser OBLIGATORIA y ÚNICA.

En PostgreSQL, unique=True crea el índice único y además un índice "_like"
(varchar_pattern_ops), que hace rápida la búsqueda por el comienzo
(LIKE 'AN-18K%') aunque haya millones de productos.

Va separado del paso 2 porque PostgreSQL no deja cambiar una tabla en la misma
transacción en la que se acaban de modificar sus filas.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_referencias_datos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='referencia',
            field=models.CharField(max_length=40, unique=True),
        ),
    ]
