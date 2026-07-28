from rest_framework.exceptions import ValidationError

from .models import Pais


def validar_codigo_pais(codigo):
    if not Pais.objects.filter(codigo=codigo).exists():
        raise ValidationError(f'"{codigo}" no es un codigo de pais valido. Ver GET /api/v1/paises.')
