from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.validators import validar_codigo_pais

from .models import Usuario


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    pais = serializers.CharField(validators=[validar_codigo_pais])

    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'correo', 'password', 'pais']

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data, provider=Usuario.PROVIDER_LOCAL, estado=Usuario.ESTADO_PENDIENTE)
        usuario.set_password(password)
        usuario.save()
        return usuario


class VerificarOTPSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    codigo = serializers.CharField(max_length=6, min_length=6)


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class LoginSerializer(TokenObtainPairSerializer):
    """
    Igual que TokenObtainPairSerializer, pero con mensajes de error especificos
    en vez del generico "No active account found with the given credentials"
    de simplejwt.
    """

    def validate(self, attrs):
        correo = attrs.get(self.username_field)
        password = attrs.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('No existe una cuenta con este correo.')

        if usuario.provider == Usuario.PROVIDER_GOOGLE:
            raise AuthenticationFailed('Esta cuenta inicia sesion con Google. Usa esa opcion para ingresar.')

        if usuario.estado != Usuario.ESTADO_ACTIVO:
            raise AuthenticationFailed(
                'Tu cuenta esta pendiente de verificacion. Revisa tu correo por el codigo OTP.'
            )

        if not usuario.check_password(password):
            raise AuthenticationFailed('Contraseña incorrecta.')

        return super().validate(attrs)


class OlvidePasswordSerializer(serializers.Serializer):
    correo = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    codigo = serializers.CharField(max_length=6, min_length=6)
    nueva_password = serializers.CharField(write_only=True, validators=[validate_password])


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    nueva_password = serializers.CharField(write_only=True, validators=[validate_password])


class UsuarioSerializer(serializers.ModelSerializer):
    pais = serializers.CharField(validators=[validar_codigo_pais])

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre_completo', 'correo', 'pais', 'foto_url',
            'peso_kg', 'provider', 'estado', 'creado_en',
        ]
        read_only_fields = ['id', 'correo', 'provider', 'estado', 'creado_en', 'foto_url']


class FotoPerfilSerializer(serializers.Serializer):
    foto = serializers.ImageField()


class FotoPerfilRespuestaSerializer(serializers.Serializer):
    foto_url = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class MensajeSerializer(serializers.Serializer):
    mensaje = serializers.CharField()


class MensajeConTokensSerializer(serializers.Serializer):
    mensaje = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
