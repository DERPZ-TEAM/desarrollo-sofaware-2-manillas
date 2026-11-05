"""
Regla nueva: una persona es CLIENTE solo si compró (en la web o en el local).

Hasta ahora, registrarse en la web creaba también una ficha de cliente. Esta
migración quita las fichas de las cuentas que NUNCA hicieron un pedido: esas
personas siguen siendo usuarios y se vuelven clientes en su primera compra
(ahí se les pide el documento).

No toca:
  - clientes con al menos un pedido (en cualquier estado);
  - clientes sin cuenta (los registró el administrador en el local);
  - clientes que están en la Papelera (el administrador decide qué hacer con ellos).
"""
from django.db import migrations
from django.db.models import Count


def quitar_clientes_sin_compras(apps, schema_editor):
    Cliente = apps.get_model('account', 'Cliente')
    sin_compras = (Cliente._base_manager
                   .filter(usuario__isnull=False, eliminado_en__isnull=True)   # lo de la Papelera se respeta
                   .annotate(n=Count('pedidos'))
                   .filter(n=0))
    Cliente._base_manager.filter(pk__in=list(sin_compras.values_list('pk', flat=True))).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_cliente_obligatorio'),
    ]

    operations = [
        # Volver atrás no recrea las fichas: se crearán solas en la próxima compra.
        migrations.RunPython(quitar_clientes_sin_compras, migrations.RunPython.noop),
    ]
