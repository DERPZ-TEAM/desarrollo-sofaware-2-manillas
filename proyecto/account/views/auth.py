"""
Vistas de AUTENTICACIÓN: registro, login (cliente y admin), perfil,
cierre de sesión y recuperación de contraseña.

Flujo JWT (JSON Web Token):
  1. El usuario envía usuario+contraseña a /api/auth/login/.
  2. Si son correctos, el backend responde dos tokens:
       - access  (dura 30 min): se envía en cada petición en la cabecera
                 "Authorization: Bearer <access>"
       - refresh (dura 1 día): sirve para pedir un access nuevo sin volver
                 a escribir la contraseña (/api/auth/refresh/).
  3. Al cerrar sesión, el refresh se pone en la "lista negra" y deja de servir.
"""
import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..permissions import es_admin
from ..serializers import (
    ActualizarPerfilSerializer,
    CambiarPasswordSerializer,
    ConfirmarRecuperacionSerializer,
    LoginSerializer,
    RegistroSerializer,
    SolicitarRecuperacionSerializer,
    UsuarioSerializer,
)

User = get_user_model()
logger = logging.getLogger('goldbracelets.auth')


class LimiteLogin(AnonRateThrottle):
    """Máximo 10 intentos de login por minuto desde la misma IP (fuerza bruta)."""
    scope = 'login'


class LimiteRecuperacion(AnonRateThrottle):
    scope = 'recuperacion'


def tokens_para(user):
    """Genera el par de tokens JWT + los datos públicos del usuario."""
    refresh = RefreshToken.for_user(user)
    refresh['rol'] = 'admin' if es_admin(user) else 'cliente'   # dato extra dentro del token
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UsuarioSerializer(user).data,
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def registro_view(request):
    """POST /api/auth/registro/  (HU-US-001)"""
    serializer = RegistroSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    datos = tokens_para(user)
    datos['detail'] = '¡Registro exitoso! Bienvenida(o) a GoldBracelets.'
    return Response(datos, status=status.HTTP_201_CREATED)


def _login(request, solo_admin):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    identificador = serializer.validated_data['username']
    password = serializer.validated_data['password']

    # Si escribió un correo, buscamos a qué usuario pertenece (HU-AU-002)
    username = identificador
    if '@' in identificador:
        dueño = User.objects.filter(email__iexact=identificador).first()
        username = dueño.username if dueño else identificador

    user = authenticate(request, username=username, password=password)
    if user is None:
        # Mismo mensaje si falla el usuario o la contraseña: no damos pistas
        return Response({'detail': 'Usuario o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Flujos separados: cada tipo de cuenta entra por su propia puerta
    if solo_admin and not es_admin(user):
        return Response(
            {'detail': 'Esta cuenta no tiene acceso de administrador.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    if not solo_admin and es_admin(user):
        return Response(
            {'detail': 'Las cuentas de administrador ingresan por el panel de gestión.', 'admin': True},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(tokens_para(user))


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LimiteLogin])
def login_view(request):
    """POST /api/auth/login/  -> solo clientes"""
    return _login(request, solo_admin=False)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LimiteLogin])
def admin_login_view(request):
    """POST /api/auth/admin/login/  -> solo administradores"""
    return _login(request, solo_admin=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/  (HU-SE-032): invalida el refresh token."""
    refresh = request.data.get('refresh')
    if refresh:
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            pass  # ya estaba vencido o invalidado: igual cerramos sesión
    return Response({'detail': 'Sesión cerrada correctamente.'})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET/PUT /api/auth/me/  (HU-US-004): ver y actualizar mis datos."""
    if request.method == 'GET':
        return Response(UsuarioSerializer(request.user).data)
    serializer = ActualizarPerfilSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UsuarioSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password_view(request):
    """POST /api/auth/password/cambiar/"""
    serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data['password'])
    request.user.save(update_fields=['password'])
    return Response({'detail': 'Contraseña actualizada. Vuelve a iniciar sesión.'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LimiteRecuperacion])
def solicitar_recuperacion_view(request):
    """POST /api/auth/password/recuperar/  (HU-US-003 paso 1)

    Genera un enlace con un token de un solo uso y lo envía por correo.
    """
    serializer = SolicitarRecuperacionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email'].lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        # Criterio de aceptación 2 de la HU-US-003
        return Response({'detail': 'Ese correo no está registrado.'}, status=status.HTTP_404_NOT_FOUND)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    enlace = f'{settings.FRONTEND_URL}/restablecer/{uid}/{token}'
    send_mail(
        subject='GoldBracelets · Recupera tu contraseña',
        message=(
            f'Hola {user.first_name or user.username},\n\n'
            f'Para crear una nueva contraseña abre este enlace:\n{enlace}\n\n'
            'Si no lo solicitaste, ignora este mensaje.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    logger.info('Enlace de recuperación generado para %s', user.username)
    respuesta = {'detail': 'Te enviamos un enlace de recuperación a tu correo.'}
    if settings.MOSTRAR_ENLACE_RECUPERACION:
        respuesta['enlace_demo'] = enlace     # solo en modo demostración
    return Response(respuesta)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LimiteRecuperacion])
def confirmar_recuperacion_view(request):
    """POST /api/auth/password/restablecer/  (HU-US-003 paso 2)"""
    serializer = ConfirmarRecuperacionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    datos = serializer.validated_data
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(datos['uid'])))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is None or not default_token_generator.check_token(user, datos['token']):
        return Response(
            {'detail': 'El enlace no es válido o ya fue usado. Solicita uno nuevo.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_password(datos['password'], user=user)
    except DjangoValidationError as exc:
        return Response({'detail': exc.messages[0], 'errors': {'password': exc.messages}}, status=400)
    user.set_password(datos['password'])
    user.save(update_fields=['password'])
    return Response({'detail': 'Contraseña actualizada. Ya puedes iniciar sesión.'})
