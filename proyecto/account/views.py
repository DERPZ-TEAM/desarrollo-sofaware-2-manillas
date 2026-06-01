from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


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
    return render(request, 'account/inicio.html')


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