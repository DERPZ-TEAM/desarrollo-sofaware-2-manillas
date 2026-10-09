from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Producto, Carrito, ItemCarrito, Categoria
from .forms import ProductoForm, CategoriaForm
from django.db.models import F, Count
from django.contrib import messages


def login_view(request):

    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('inicio')

        else:
            return render(request, 'account/login.html', {
                'error': 'Usuario incorrecto'
            })

    return render(request, 'account/login.html')


def registro(request):

    if request.method == 'POST':

        username = request.POST['username']
        email = request.POST['email'].lower()
        password = request.POST['password']

        primer_nombre = request.POST['primer_nombre'].title()
        segundo_nombre = request.POST['segundo_nombre'].title()
        apellidos = request.POST['apellidos'].title()

        usuario_existente = User.objects.filter(
            username=username
        ).first()

        if usuario_existente:

            if usuario_existente.is_active == False:

                usuario_existente.is_active = True
                usuario_existente.email = email
                usuario_existente.set_password(password)

                usuario_existente.save()

                return redirect('login')

            return render(request, 'account/registro.html', {
                'error': 'El usuario ya existe'
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=primer_nombre + " " + segundo_nombre,
            last_name=apellidos
        )

        return redirect('login')

    return render(request, 'account/registro.html')


@login_required
def inicio(request):

    productos = Producto.objects.filter(
        activo=True
    ).select_related('categoria')

    return render(
        request,
        'account/inicio.html',
        {
            'productos': productos
        }
    )


def cerrar_sesion(request):
    logout(request)
    return redirect('login')


@login_required
def actualizar_usuario(request):

    usuario = request.user

    if request.method == 'POST':

        nuevo_username = request.POST['username']
        nuevo_email = request.POST['email']

        usuario.username = nuevo_username
        usuario.email = nuevo_email

        usuario.save()

        return redirect('inicio')

    return render(request, 'account/actualizar_usuario.html', {
        'usuario': usuario
    })


@login_required
def agregar_carrito(request, producto_id):

    producto = get_object_or_404(Producto, id=producto_id, activo=True)

    carrito, creado = Carrito.objects.get_or_create(
        usuario=request.user
    )

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not creado:
        item.cantidad += 1
        item.save()

    return redirect('inicio')


@login_required
def ver_carrito(request):

    carrito = Carrito.objects.filter(
        usuario=request.user
    ).first()

    items = []

    total = 0

    if carrito:

        items = ItemCarrito.objects.filter(
            carrito=carrito
        )

        for item in items:
            total += item.producto.precio * item.cantidad

    return render(
        request,
        'account/carrito.html',
        {
            'items': items,
            'total': total
        }
    )


@login_required
def eliminar_item(request, item_id):

    item = get_object_or_404(
        ItemCarrito,
        id=item_id,
        carrito__usuario=request.user
    )

    item.delete()

    return redirect('carrito')


@login_required
def aumentar_cantidad(request, item_id):

    item = get_object_or_404(
        ItemCarrito,
        id=item_id,
        carrito__usuario=request.user
    )

    item.cantidad += 1

    item.save()

    return redirect('carrito')


@login_required
def disminuir_cantidad(request, item_id):

    item = get_object_or_404(
        ItemCarrito,
        id=item_id,
        carrito__usuario=request.user
    )

    if item.cantidad > 1:

        item.cantidad -= 1

        item.save()

    else:

        item.delete()

    return redirect('carrito')


@login_required
def vaciar_carrito(request):

    carrito = Carrito.objects.filter(
        usuario=request.user
    ).first()

    if carrito:

        ItemCarrito.objects.filter(
            carrito=carrito
        ).delete()

    return redirect('carrito')


@login_required
def finalizar_compra(request):

    carrito = Carrito.objects.filter(
        usuario=request.user
    ).first()

    if carrito:

        ItemCarrito.objects.filter(
            carrito=carrito
        ).delete()

    messages.success(
        request,
        'Compra realizada exitosamente.'
    )

    return redirect('inicio')


# ---------------------------------------------------------------------
# Gestión de productos y categorías (administrador)
# HU-IN-006 registrar, HU-IN-007 editar, HU-IN-008 eliminar,
# HU-IN-010 clasificar por categoría
# ---------------------------------------------------------------------

def es_administrador(user):
    return user.is_staff


def solo_admin(vista):
    """Exige sesión iniciada y rol de administrador.
    Si el usuario no es administrador lo manda a la tienda."""
    return login_required(
        user_passes_test(es_administrador, login_url='inicio')(vista)
    )


# ---------- Productos ----------

@solo_admin
def gestion_productos(request):

    categoria_id = request.GET.get('categoria', '')

    productos = Producto.objects.select_related('categoria').order_by('nombre')

    if categoria_id == 'sin':
        productos = productos.filter(categoria__isnull=True)
    elif categoria_id.isdigit():
        productos = productos.filter(categoria_id=int(categoria_id))

    return render(
        request,
        'account/gestion_productos.html',
        {
            'productos': productos,
            'categorias': Categoria.objects.order_by('nombre'),
            'categoria_activa': categoria_id,
        }
    )


@solo_admin
def registrar_producto(request):

    if request.method == 'POST':

        form = ProductoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Producto registrado exitosamente.')
            return redirect('gestion_productos')

        messages.error(request, 'Revisa los campos, hay información inválida o incompleta.')

    else:
        form = ProductoForm()

    return render(
        request,
        'account/producto_form.html',
        {
            'form': form,
            'titulo': 'Registrar producto'
        }
    )


@solo_admin
def editar_producto(request, producto_id):

    producto = Producto.objects.filter(id=producto_id).first()

    if not producto:
        messages.error(request, 'El producto no existe.')
        return redirect('gestion_productos')

    if request.method == 'POST':

        form = ProductoForm(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            form.save()
            messages.success(request, 'Información del producto actualizada correctamente.')
            return redirect('gestion_productos')

        messages.error(request, 'Revisa los campos, hay información inválida o incompleta.')

    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        'account/producto_form.html',
        {
            'form': form,
            'titulo': 'Editar producto',
            'producto': producto
        }
    )


@solo_admin
def eliminar_producto(request, producto_id):

    producto = Producto.objects.filter(id=producto_id).first()

    if not producto:
        messages.error(request, 'El producto no existe.')
        return redirect('gestion_productos')

    # GET: pide confirmación. POST: elimina de verdad.
    if request.method == 'POST':
        producto.imagen.delete(save=False)
        producto.delete()
        messages.success(request, 'Producto eliminado del catálogo.')
        return redirect('gestion_productos')

    return render(
        request,
        'account/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar producto',
            'nombre': producto.nombre,
            'aviso': 'Se quitará del catálogo y de los carritos donde esté. Esta acción no se puede deshacer.',
            'volver': 'gestion_productos',
        }
    )


# ---------- Categorías ----------

@solo_admin
def gestion_categorias(request):

    categorias = Categoria.objects.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')

    return render(
        request,
        'account/gestion_categorias.html',
        {
            'categorias': categorias
        }
    )


@solo_admin
def registrar_categoria(request):

    if request.method == 'POST':

        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada.')
            return redirect('gestion_categorias')

        messages.error(request, 'Revisa el nombre de la categoría.')

    else:
        form = CategoriaForm()

    return render(
        request,
        'account/categoria_form.html',
        {
            'form': form,
            'titulo': 'Nueva categoría'
        }
    )


@solo_admin
def editar_categoria(request, categoria_id):

    categoria = Categoria.objects.filter(id=categoria_id).first()

    if not categoria:
        messages.error(request, 'La categoría no existe.')
        return redirect('gestion_categorias')

    if request.method == 'POST':

        form = CategoriaForm(request.POST, instance=categoria)

        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada.')
            return redirect('gestion_categorias')

        messages.error(request, 'Revisa el nombre de la categoría.')

    else:
        form = CategoriaForm(instance=categoria)

    return render(
        request,
        'account/categoria_form.html',
        {
            'form': form,
            'titulo': 'Editar categoría'
        }
    )


@solo_admin
def eliminar_categoria(request, categoria_id):

    categoria = Categoria.objects.filter(id=categoria_id).first()

    if not categoria:
        messages.error(request, 'La categoría no existe.')
        return redirect('gestion_categorias')

    if request.method == 'POST':
        categoria.delete()  # los productos quedan "sin categoría"
        messages.success(request, 'Categoría eliminada.')
        return redirect('gestion_categorias')

    return render(
        request,
        'account/confirmar_eliminar.html',
        {
            'titulo': 'Eliminar categoría',
            'nombre': categoria.nombre,
            'aviso': 'Los productos de esta categoría no se borran: quedan "sin categoría".',
            'volver': 'gestion_categorias',
        }
    )
