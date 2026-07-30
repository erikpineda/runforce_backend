from django.core.files.storage import default_storage
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

from .models import CodigoOTP, Usuario
from .serializers import (
    CambiarPasswordSerializer,
    FotoPerfilRespuestaSerializer,
    FotoPerfilSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
    MensajeConTokensSerializer,
    MensajeSerializer,
    OlvidePasswordSerializer,
    RegistroSerializer,
    ResetPasswordSerializer,
    TokenSerializer,
    UsuarioSerializer,
    VerificarOTPSerializer,
)
from .services import generar_y_enviar_otp, validar_google_id_token, validar_otp

RATE_AUTH = 'ip'
TAG_AUTH = 'Autenticacion'
TAG_USUARIOS = 'Usuarios'


def _tokens_para(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def _revocar_refresh_tokens(usuario):
    for outstanding in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=outstanding)


@extend_schema_view(
    post=extend_schema(
        tags=[TAG_AUTH],
        summary='Registrar nuevo usuario',
        description=(
            'Crea un usuario en estado `pendiente` y envia un codigo OTP de 6 digitos al correo '
            'para completar la activacion en `/auth/verificar-otp`.'
        ),
        responses={201: MensajeSerializer},
    )
)
@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        generar_y_enviar_otp(usuario, CodigoOTP.TIPO_REGISTRO)
        return Response(
            {'mensaje': 'Registro exitoso. Revisa tu correo para el codigo de verificacion.'},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class VerificarOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=[TAG_AUTH],
        summary='Verificar codigo OTP de registro',
        description='Valida el OTP enviado por correo tras el registro y activa la cuenta, devolviendo tokens JWT.',
        request=VerificarOTPSerializer,
        responses={200: TokenSerializer},
    )
    def post(self, request):
        serializer = VerificarOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            usuario = Usuario.objects.get(correo=datos['correo'])
        except Usuario.DoesNotExist:
            raise ValidationError('Usuario no encontrado.')

        validar_otp(usuario, datos['codigo'], CodigoOTP.TIPO_REGISTRO)

        usuario.estado = Usuario.ESTADO_ACTIVO
        usuario.save(update_fields=['estado'])

        return Response(_tokens_para(usuario))


@extend_schema(
    tags=[TAG_AUTH],
    summary='Login con correo y password',
    description=(
        'Autentica un usuario local activo y devuelve un par de tokens JWT (access + refresh). '
        'Mensajes de error especificos: correo inexistente, cuenta pendiente de verificacion, '
        'cuenta de Google (sin password), o contraseña incorrecta.'
    ),
    responses={200: TokenSerializer},
)
@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class LoginView(TokenObtainPairView):
    """Login local. Usa el campo `correo` (USERNAME_FIELD) y `password`."""
    serializer_class = LoginSerializer


@extend_schema(tags=[TAG_AUTH], summary='Refrescar access token')
class TokenRefreshView(SimpleJWTTokenRefreshView):
    pass


@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=[TAG_AUTH],
        summary='Login / registro con Google Sign-In',
        description=(
            'Valida el `idToken` de Google contra los servidores de Google. Si el usuario no existe, '
            'lo crea activo con `provider=google`. Devuelve tokens JWT. Si ya existe una cuenta local '
            '(`provider=local`) con ese correo, se rechaza para evitar que Google tome control de una '
            'cuenta que no le pertenece.'
        ),
        request=GoogleAuthSerializer,
        responses={200: TokenSerializer},
        examples=[OpenApiExample('Request', value={'id_token': 'eyJhbGciOi...'}, request_only=True)],
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idinfo = validar_google_id_token(serializer.validated_data['id_token'])
        google_id = idinfo['sub']
        correo = idinfo.get('email')

        usuario = Usuario.objects.filter(google_id=google_id).first()

        if usuario is None:
            usuario_existente = Usuario.objects.filter(correo=correo).first()

            if usuario_existente is not None:
                if usuario_existente.provider == Usuario.PROVIDER_LOCAL:
                    raise ValidationError(
                        'Ya existe una cuenta local con este correo. Inicia sesion con tu password '
                        'en vez de con Google.'
                    )
                # Cuenta google preexistente sin google_id (no deberia pasar, pero por las dudas
                # se vincula en vez de crear un duplicado).
                usuario_existente.google_id = google_id
                usuario_existente.estado = Usuario.ESTADO_ACTIVO
                usuario_existente.save(update_fields=['google_id', 'estado'])
                usuario = usuario_existente
            else:
                usuario = Usuario.objects.create(
                    correo=correo,
                    nombre_completo=idinfo.get('name', correo),
                    pais='',
                    foto_url=idinfo.get('picture'),
                    provider=Usuario.PROVIDER_GOOGLE,
                    google_id=google_id,
                    estado=Usuario.ESTADO_ACTIVO,
                )

        return Response(_tokens_para(usuario))


@method_decorator(ratelimit(key=RATE_AUTH, rate='5/m', method='POST', block=True), name='post')
class OlvidePasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=[TAG_AUTH],
        summary='Solicitar codigo de recuperacion de password',
        description=(
            'Envia un OTP tipo `reset_password` al correo, si pertenece a un usuario local. '
            'Mensajes especificos: correo inexistente, o cuenta de Google (sin password que restablecer). '
            'Nota: esto revela si un correo esta registrado (se prioriza la claridad del mensaje '
            'sobre ocultar la existencia de la cuenta).'
        ),
        request=OlvidePasswordSerializer,
        responses={200: MensajeSerializer},
    )
    def post(self, request):
        serializer = OlvidePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            usuario = Usuario.objects.get(correo=serializer.validated_data['correo'])
        except Usuario.DoesNotExist:
            raise ValidationError('No existe una cuenta con este correo.')

        if usuario.provider == Usuario.PROVIDER_GOOGLE:
            raise ValidationError('Esta cuenta inicio sesion con Google. No tiene password para restablecer.')

        generar_y_enviar_otp(usuario, CodigoOTP.TIPO_RESET_PASSWORD)

        return Response({'mensaje': 'Se envio un codigo de recuperacion a tu correo.'})


@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=[TAG_AUTH],
        summary='Restablecer password con OTP',
        description='Valida el OTP tipo `reset_password`, cambia el password y revoca los refresh tokens previos.',
        request=ResetPasswordSerializer,
        responses={200: MensajeSerializer},
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            usuario = Usuario.objects.get(correo=datos['correo'])
        except Usuario.DoesNotExist:
            raise ValidationError('Usuario no encontrado.')

        if usuario.provider == Usuario.PROVIDER_GOOGLE:
            raise ValidationError('Esta cuenta inicio sesion con Google. No tiene password para restablecer.')

        validar_otp(usuario, datos['codigo'], CodigoOTP.TIPO_RESET_PASSWORD)

        usuario.set_password(datos['nueva_password'])
        usuario.save(update_fields=['password'])
        _revocar_refresh_tokens(usuario)

        return Response({'mensaje': 'Password actualizado correctamente.'})


@method_decorator(ratelimit(key=RATE_AUTH, rate='10/m', method='POST', block=True), name='post')
class CambiarPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_USUARIOS],
        summary='Cambiar password (logueado)',
        description=(
            'Cambia el password del usuario autenticado, verificando el password actual. '
            'No disponible para cuentas `provider=google`. Revoca los refresh tokens previos y '
            'devuelve un par de tokens nuevo para que la sesion actual siga funcionando.'
        ),
        request=CambiarPasswordSerializer,
        responses={200: MensajeConTokensSerializer},
    )
    def post(self, request):
        usuario = request.user

        if usuario.provider == Usuario.PROVIDER_GOOGLE:
            raise ValidationError('Esta cuenta inicio sesion con Google. No tiene password para cambiar.')

        serializer = CambiarPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        if not usuario.check_password(datos['password_actual']):
            raise ValidationError('La contraseña actual es incorrecta.')

        usuario.set_password(datos['nueva_password'])
        usuario.save(update_fields=['password'])
        _revocar_refresh_tokens(usuario)

        return Response({'mensaje': 'Password actualizado correctamente.', **_tokens_para(usuario)})


@extend_schema_view(
    get=extend_schema(tags=[TAG_USUARIOS], summary='Obtener mi perfil'),
    put=extend_schema(tags=[TAG_USUARIOS], summary='Actualizar mi perfil (reemplazo completo)'),
    patch=extend_schema(tags=[TAG_USUARIOS], summary='Actualizar mi perfil (parcial)'),
)
class UsuarioMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class FotoPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_USUARIOS],
        summary='Subir foto de perfil',
        description='Sube una imagen (multipart/form-data) y actualiza `foto_url` del usuario autenticado.',
        request=FotoPerfilSerializer,
        responses={200: FotoPerfilRespuestaSerializer},
    )
    def post(self, request):
        serializer = FotoPerfilSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        archivo = serializer.validated_data['foto']
        nombre = f'perfiles/{request.user.id}/{archivo.name}'
        ruta_guardada = default_storage.save(nombre, archivo)

        usuario = request.user
        usuario.foto_url = default_storage.url(ruta_guardada)
        usuario.save(update_fields=['foto_url'])

        return Response({'foto_url': usuario.foto_url})
