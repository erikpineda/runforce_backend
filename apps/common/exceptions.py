from django_ratelimit.exceptions import Ratelimited
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def manejador_excepciones(exc, context):
    """Envuelve las respuestas de error de DRF en un formato consistente."""
    if isinstance(exc, Ratelimited):
        return Response(
            {'error': True, 'detalle': 'Demasiadas solicitudes. Intenta de nuevo mas tarde.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'error': True,
            'detalle': response.data,
        }

    return response
