from django.db import models


class Pais(models.Model):
    codigo = models.CharField(max_length=2, unique=True, help_text='Codigo ISO 3166-1 alpha-2, ej. HN')
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'paises'
        ordering = ['nombre']
        verbose_name = 'Pais'
        verbose_name_plural = 'Paises'

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'
