from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.runs.models import Carrera
from apps.social.services import _restar_meses


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

    def test_ranking_desplazamiento_muestra_mes_anterior(self):
        # timedelta(days=35) no sirve aqui: segun el dia del mes en que corra
        # el test, 35 dias atras puede caer dos meses atras en vez de uno.
        # Se usa el mismo helper que la vista para ubicar la fecha sin ambiguedad.
        mes_pasado = _restar_meses(timezone.now(), 1)
        Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta vieja', distancia_km='7.000',
            duracion_seg=2000, iniciada_en=mes_pasado,
        )

        respuesta_actual = self.client.get('/api/v1/ranking?periodo=mes')
        self.assertEqual(respuesta_actual.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta_actual.data), 0)

        respuesta_anterior = self.client.get('/api/v1/ranking?periodo=mes&desplazamiento=1')
        self.assertEqual(respuesta_anterior.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta_anterior.data), 1)
        self.assertEqual(respuesta_anterior.data[0]['usuario_id'], self.usuario.id)

    def test_ranking_rechaza_desplazamiento_negativo(self):
        respuesta = self.client.get('/api/v1/ranking?desplazamiento=-1')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ranking_rechaza_desplazamiento_fuera_de_rango(self):
        respuesta = self.client.get('/api/v1/ranking?desplazamiento=121')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
