"""
Paso 3 de 3: cierra las reglas, una vez que los datos ya están en su lugar.

- Todo pedido DEBE tener cliente (ya no puede quedar vacío).
- Quita del perfil los datos personales que ahora viven en la tabla cliente.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_datos_clientes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido',
            name='cliente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pedidos', to='account.cliente'),
        ),
        migrations.RemoveField(model_name='perfil', name='telefono'),
        migrations.RemoveField(model_name='perfil', name='direccion'),
        migrations.RemoveField(model_name='perfil', name='ciudad'),
        migrations.RemoveField(model_name='perfil', name='departamento'),
    ]
