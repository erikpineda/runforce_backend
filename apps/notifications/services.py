import logging

import requests
from django.conf import settings

from .models import Dispositivo, Notificacion

logger = logging.getLogger(__name__)


def enviar_push(player_ids, mensaje, titulo='RunForce'):
    if not player_ids or not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_REST_API_KEY:
        return None

    payload = {
        'app_id': settings.ONESIGNAL_APP_ID,
        'include_player_ids': player_ids,
        'headings': {'en': titulo},
        'contents': {'en': mensaje},
    }
    headers = {
        'Authorization': f'Basic {settings.ONESIGNAL_REST_API_KEY}',
        'Content-Type': 'application/json',
    }

    try:
        respuesta = requests.post(settings.ONESIGNAL_API_URL, json=payload, headers=headers, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException:
        logger.exception('Fallo al enviar notificacion push via OneSignal')
        return None


def crear_notificacion(usuario, tipo, mensaje):
    notificacion = Notificacion.objects.create(usuario=usuario, tipo=tipo, mensaje=mensaje)

    player_ids = list(
        Dispositivo.objects.filter(usuario=usuario).values_list('onesignal_player_id', flat=True)
    )
    enviar_push(player_ids, mensaje)

    return notificacion


def notificar_solicitud_amistad(origen, destino):
    return crear_notificacion(
        destino, Notificacion.TIPO_AMISTAD, f'{origen.nombre_completo} te agrego como amigo.'
    )


def notificar_logro(usuario, mensaje):
    return crear_notificacion(usuario, Notificacion.TIPO_LOGRO, mensaje)


def notificar_ranking_superado(usuario, mensaje):
    return crear_notificacion(usuario, Notificacion.TIPO_RANKING, mensaje)


def notificar_inactividad(usuario):
    return crear_notificacion(
        usuario, Notificacion.TIPO_INACTIVIDAD,
        'Han pasado varios dias sin registrar una carrera. ¡Vuelve a correr!',
    )
