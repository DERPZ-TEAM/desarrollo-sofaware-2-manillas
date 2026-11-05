"""
Paso 2 de 3: pasa los datos existentes a la tabla cliente, sin perder nada.

- Por cada usuario con rol "cliente" (y por cualquier usuario que tenga pedidos)
  crea su Cliente, copiando nombre, correo, teléfono y dirección del perfil.
  El documento queda vacío: se le pedirá antes de su próxima compra.
- Cada pedido queda asignado al cliente de quien lo registró.
"""
from django.db import migrations


def crear_clientes(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Perfil = apps.get_model('account', 'Perfil')
    Cliente = apps.get_model('account', 'Cliente')
    Pedido = apps.get_model('account', 'Pedido')

    con_pedidos = set(Pedido.objects.values_list('registrado_por_id', flat=True))
    for user in User.objects.all():
        perfil = Perfil.objects.filter(usuario=user).first()
        es_cliente = perfil is None or perfil.rol == 'cliente'
        if not (es_cliente or user.id in con_pedidos):
            continue                     # administradores sin compras: no son clientes
        Cliente.objects.get_or_create(
            usuario=user,
            defaults={
                'nombres': user.first_name or user.username,
                'apellidos': user.last_name,
                'correo': user.email,
                'telefono': getattr(perfil, 'telefono', '') or '',
                'direccion': getattr(perfil, 'direccion', '') or '',
                'ciudad': getattr(perfil, 'ciudad', '') or '',
                'departamento': getattr(perfil, 'departamento', '') or '',
            },
        )

    for cliente in Cliente.objects.exclude(usuario=None):
        Pedido.objects.filter(registrado_por=cliente.usuario, cliente=None).update(cliente=cliente)


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_cliente_y_papelera'),
    ]

    operations = [
        migrations.RunPython(crear_clientes, migrations.RunPython.noop),
    ]
