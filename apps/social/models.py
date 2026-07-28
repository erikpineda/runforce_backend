from django.conf import settings
from django.db import models


class Amistad(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_ACEPTADA = 'aceptada'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ACEPTADA, 'Aceptada'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amistades_iniciadas'
    )
    amigo = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='amistades_recibidas'
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_ACEPTADA)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'amistades'
        ordering = ['-creado_en']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'amigo'], name='amistad_unica_por_par'),
        ]

    def __str__(self):
        return f'{self.usuario.correo} -> {self.amigo.correo} ({self.estado})'
