"""
Paso 1 de 3: estructura nueva (no mueve datos todavía).

- Crea la tabla "cliente" (la persona que compra), separada del usuario (la cuenta).
- Agrega "eliminado_en" a productos y categorías para el borrado lógico (papelera).
- En pedido: agrega "cliente" (de quién es la compra; vacío por ahora) y renombra
  "usuario" a "registrado_por" (quién la registró). Renombrar conserva los datos.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_catalogo_demo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('tipo_documento', models.CharField(choices=[('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'), ('TI', 'Tarjeta de identidad'), ('PAS', 'Pasaporte')], default='CC', max_length=4)),
                ('numero_documento', models.CharField(blank=True, default='', max_length=20)),
                ('nombres', models.CharField(max_length=80)),
                ('apellidos', models.CharField(blank=True, default='', max_length=80)),
                ('correo', models.EmailField(blank=True, default='', max_length=254)),
                ('telefono', models.CharField(blank=True, default='', max_length=20)),
                ('direccion', models.CharField(blank=True, default='', max_length=200)),
                ('ciudad', models.CharField(blank=True, default='', max_length=80)),
                ('departamento', models.CharField(blank=True, default='', max_length=80)),
                ('eliminado_en', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cliente', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'cliente',
                'ordering': ['nombres', 'apellidos'],
                'constraints': [
                    models.UniqueConstraint(
                        condition=models.Q(('numero_documento', ''), _negated=True),
                        fields=('tipo_documento', 'numero_documento'),
                        name='cliente_documento_unico',
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name='producto',
            name='eliminado_en',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='categoria',
            name='eliminado_en',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='pedido',
            name='cliente',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pedidos', to='account.cliente'),
        ),
        migrations.RenameField(
            model_name='pedido',
            old_name='usuario',
            new_name='registrado_por',
        ),
        migrations.AlterField(
            model_name='pedido',
            name='registrado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos_registrados', to=settings.AUTH_USER_MODEL),
        ),
    ]
