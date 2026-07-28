from django.conf import settings
from django.db import models


class Dispositivo(models.Model):
    PLATAFORMA_ANDROID = 'android'
    PLATAFORMA_CHOICES = [
        (PLATAFORMA_ANDROID, 'Android'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dispositivos')
    onesignal_player_id = models.CharField(max_length=255)
    plataforma = models.CharField(max_length=20, choices=PLATAFORMA_CHOICES, default=PLATAFORMA_ANDROID)

    class Meta:
        db_table = 'dispositivos'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'onesignal_player_id'], name='dispositivo_unico_por_usuario'),
        ]

    def __str__(self):
        return f'{self.usuario.correo} ({self.plataforma})'


class Notificacion(models.Model):
    TIPO_LOGRO = 'logro'
    TIPO_RANKING = 'ranking'
    TIPO_AMISTAD = 'amistad'
    TIPO_INACTIVIDAD = 'inactividad'
    TIPO_CHOICES = [
        (TIPO_LOGRO, 'Logro'),
        (TIPO_RANKING, 'Ranking'),
        (TIPO_AMISTAD, 'Amistad'),
        (TIPO_INACTIVIDAD, 'Inactividad'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensaje = models.CharField(max_length=255)
    leido = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.tipo} -> {self.usuario.correo}'
