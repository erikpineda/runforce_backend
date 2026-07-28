from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone


def calcular_ritmo_seg_km(distancia_km, duracion_seg):
    if not distancia_km:
        return 0
    return int(round(Decimal(duracion_seg) / Decimal(distancia_km)))


def calcular_calorias(usuario, distancia_km):
    if usuario.peso_kg:
        return int(round(Decimal(usuario.peso_kg) * Decimal(distancia_km) * Decimal(settings.CALORIAS_FACTOR_CON_PESO)))
    return int(round(Decimal(distancia_km) * Decimal(settings.CALORIAS_FACTOR_SIN_PESO)))


def rango_mes(fecha):
    inicio = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)
    return inicio, fin


def rango_semana(fecha):
    inicio = (fecha - timedelta(days=fecha.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=7)
    return inicio, fin


def resumen_periodo(queryset, usuario, desde, hasta):
    carreras = queryset.filter(usuario=usuario, iniciada_en__gte=desde, iniciada_en__lt=hasta)
    agregados = carreras.aggregate(
        km_totales=Sum('distancia_km'),
        calorias_totales=Sum('calorias'),
        conteo_carreras=Count('id'),
    )
    return {
        'km_totales': agregados['km_totales'] or Decimal('0'),
        'calorias_totales': agregados['calorias_totales'] or 0,
        'conteo_carreras': agregados['conteo_carreras'] or 0,
    }


def mes_actual_y_anterior(ahora=None):
    ahora = ahora or timezone.now()
    inicio_actual, fin_actual = rango_mes(ahora)
    ultimo_dia_mes_anterior = inicio_actual - timedelta(days=1)
    inicio_anterior, _ = rango_mes(ultimo_dia_mes_anterior)
    return (inicio_actual, fin_actual), (inicio_anterior, inicio_actual)


def semana_actual_y_anterior(ahora=None):
    ahora = ahora or timezone.now()
    inicio_actual, fin_actual = rango_semana(ahora)
    inicio_anterior = inicio_actual - timedelta(days=7)
    return (inicio_actual, fin_actual), (inicio_anterior, inicio_actual)
