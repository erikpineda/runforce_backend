from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.runs.models import Carrera
from apps.notifications.models import Notificacion


class NotificacionesTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='runner@example.com', password='clave-segura-123',
            nombre_completo='Runner', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.client.force_authenticate(user=self.usuario)

    def test_registrar_dispositivo(self):
        respuesta = self.client.post('/api/v1/dispositivos', {
            'onesignal_player_id': 'player-123',
            'plataforma': 'android',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_logro_por_5km_acumulados(self):
        Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta', distancia_km='5.000',
            duracion_seg=1500, iniciada_en=timezone.now(),
        )
        notificaciones = Notificacion.objects.filter(usuario=self.usuario, tipo=Notificacion.TIPO_LOGRO)
        self.assertEqual(notificaciones.count(), 1)

    def test_marcar_notificacion_leida(self):
        notificacion = Notificacion.objects.create(
            usuario=self.usuario, tipo=Notificacion.TIPO_AMISTAD, mensaje='Prueba',
        )
        respuesta = self.client.put(f'/api/v1/notificaciones/{notificacion.id}/leido')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        notificacion.refresh_from_db()
        self.assertTrue(notificacion.leido)
