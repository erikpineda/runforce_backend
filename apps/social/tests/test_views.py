from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.runs.models import Carrera


class RankingTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='yo@example.com', password='clave-segura-123',
            nombre_completo='Yo', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.amigo = Usuario.objects.create_user(
            correo='amigo@example.com', password='clave-segura-123',
            nombre_completo='Amigo', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.client.force_authenticate(user=self.usuario)

    def test_agregar_amigo_es_reciproco(self):
        respuesta = self.client.post('/api/v1/amigos', {'amigo_id': self.amigo.id})
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        respuesta_lista = self.client.get('/api/v1/amigos')
        self.assertEqual(len(respuesta_lista.data), 1)

        self.client.force_authenticate(user=self.amigo)
        respuesta_lista_amigo = self.client.get('/api/v1/amigos')
        self.assertEqual(len(respuesta_lista_amigo.data), 1)

    def test_ranking_incluye_amigos_y_uno_mismo(self):
        self.client.post('/api/v1/amigos', {'amigo_id': self.amigo.id})
        Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta', distancia_km='5.000',
            duracion_seg=1500, iniciada_en=timezone.now(),
        )
        Carrera.objects.create(
            usuario=self.amigo, titulo='Ruta amigo', distancia_km='10.000',
            duracion_seg=3000, iniciada_en=timezone.now(),
        )
        respuesta = self.client.get('/api/v1/ranking?periodo=mes')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data), 2)
        self.assertEqual(respuesta.data[0]['usuario_id'], self.amigo.id)
