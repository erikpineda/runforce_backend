from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    PROVIDER_LOCAL = 'local'
    PROVIDER_GOOGLE = 'google'
    PROVIDER_CHOICES = [
        (PROVIDER_LOCAL, 'Local'),
        (PROVIDER_GOOGLE, 'Google'),
    ]

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_ACTIVO = 'activo'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ACTIVO, 'Activo'),
    ]

    nombre_completo = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)
    pais = models.CharField(max_length=100)
    foto_url = models.URLField(null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    meta_racha_semanal = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text='Dias por semana que el usuario se propone correr, para mantener su racha.',
    )
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default=PROVIDER_LOCAL)
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    is_staff = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre_completo', 'pais']

    class Meta:
        db_table = 'usuarios'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.nombre_completo} <{self.correo}>'

    @property
    def is_active(self):
        return self.estado == self.ESTADO_ACTIVO


class CodigoOTP(models.Model):
    TIPO_REGISTRO = 'registro'
    TIPO_RESET_PASSWORD = 'reset_password'
    TIPO_CHOICES = [
        (TIPO_REGISTRO, 'Registro'),
        (TIPO_RESET_PASSWORD, 'Reset de password'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='codigos_otp')
    codigo = models.CharField(max_length=6)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    intentos = models.IntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'codigos_otp'
        ordering = ['-creado_en']

    def __str__(self):
        return f'OTP {self.tipo} para {self.usuario.correo}'
