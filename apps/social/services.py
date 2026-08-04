from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from apps.runs.models import Carrera
from apps.runs.services import mes_actual_y_anterior, semana_actual_y_anterior

from .models import Amistad

Usuario = get_user_model()


def ids_amigos(usuario):
    return list(
        Amistad.objects.filter(usuario=usuario, estado=Amistad.ESTADO_ACEPTADA).values_list('amigo_id', flat=True)
    )


def agregar_amigo(usuario, amigo):
    Amistad.objects.get_or_create(
        usuario=usuario, amigo=amigo, defaults={'estado': Amistad.ESTADO_ACEPTADA}
    )
    Amistad.objects.get_or_create(
        usuario=amigo, amigo=usuario, defaults={'estado': Amistad.ESTADO_ACEPTADA}
    )


def _restar_meses(fecha, meses):
    """Retrocede 'meses' meses calendario. rango_mes() solo usa año/mes de
    la fecha que recibe (siempre fija el día en 1), asi que no hace falta
    preservar el día original ni lidiar con meses de distinta longitud."""
    mes_total = fecha.month - 1 - meses
    anio = fecha.year + mes_total // 12
    mes = mes_total % 12 + 1
    return fecha.replace(year=anio, month=mes, day=1)


def _rango_periodo(periodo, desplazamiento=0):
    ahora = timezone.now()
    if periodo == 'semana':
        if desplazamiento:
            ahora = ahora - timedelta(days=7 * desplazamiento)
        (inicio, fin), _ = semana_actual_y_anterior(ahora)
    else:
        if desplazamiento:
            ahora = _restar_meses(ahora, desplazamiento)
        (inicio, fin), _ = mes_actual_y_anterior(ahora)
    return inicio, fin


def construir_ranking(usuario, pais=None, periodo='mes', desplazamiento=0):
    inicio, fin = _rango_periodo(periodo, desplazamiento)

    if pais:
        usuarios_qs = Usuario.objects.filter(pais=pais, estado=Usuario.ESTADO_ACTIVO)
    else:
        ids = ids_amigos(usuario) + [usuario.id]
        usuarios_qs = Usuario.objects.filter(id__in=ids)

    ranking = (
        Carrera.objects.filter(usuario__in=usuarios_qs, iniciada_en__gte=inicio, iniciada_en__lt=fin)
        .values('usuario_id', 'usuario__nombre_completo', 'usuario__pais')
        .annotate(km_totales=Sum('distancia_km'))
        .order_by('-km_totales')
    )

    return [
        {
            'usuario_id': fila['usuario_id'],
            'nombre_completo': fila['usuario__nombre_completo'],
            'pais': fila['usuario__pais'],
            'km_totales': fila['km_totales'] or 0,
        }
        for fila in ranking
    ]
