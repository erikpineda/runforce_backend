from django.conf import settings
from django.db import models

from .services import calcular_calorias, calcular_ritmo_seg_km


class Carrera(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carreras')
    titulo = models.CharField(max_length=150)
    distancia_km = models.DecimalField(max_digits=6, decimal_places=3)
    duracion_seg = models.PositiveIntegerField()
    ritmo_seg_km = models.PositiveIntegerField(editable=False)
    calorias = models.PositiveIntegerField(editable=False)
    ruta_geojson = models.JSONField(default=list, blank=True)
    elevacion_m = models.IntegerField(null=True, blank=True)
    iniciada_en = models.DateTimeField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carreras'
        ordering = ['-iniciada_en']

    def __str__(self):
        return f'{self.titulo} ({self.usuario.correo})'

    def save(self, *args, **kwargs):
        self.ritmo_seg_km = calcular_ritmo_seg_km(self.distancia_km, self.duracion_seg)
        self.calorias = calcular_calorias(self.usuario, self.distancia_km)
        super().save(*args, **kwargs)
