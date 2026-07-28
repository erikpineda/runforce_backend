from django.contrib.auth import get_user_model
from django.db.models import Sum

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


def _rango_periodo(periodo):
    if periodo == 'semana':
        (inicio, fin), _ = semana_actual_y_anterior()
    else:
        (inicio, fin), _ = mes_actual_y_anterior()
    return inicio, fin


def construir_ranking(usuario, pais=None, periodo='mes'):
    inicio, fin = _rango_periodo(periodo)

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
