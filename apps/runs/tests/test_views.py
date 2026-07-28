from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.runs.models import Carrera


class CarreraViewTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='runner@example.com', password='clave-segura-123',
            nombre_completo='Runner', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.otro_usuario = Usuario.objects.create_user(
            correo='otro@example.com', password='clave-segura-123',
            nombre_completo='Otro', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.client.force_authenticate(user=self.usuario)

    def test_crear_carrera(self):
        respuesta = self.client.post('/api/v1/carreras', {
            'titulo': 'Ruta matutina',
            'distancia_km': '5.000',
            'duracion_seg': 1500,
            'ruta_geojson': [],
            'iniciada_en': timezone.now().isoformat(),
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['ritmo_seg_km'], 300)

    def test_no_puede_ver_carrera_de_otro_usuario(self):
        carrera_ajena = Carrera.objects.create(
            usuario=self.otro_usuario, titulo='Ajena', distancia_km='3.000',
            duracion_seg=900, iniciada_en=timezone.now(),
        )
        respuesta = self.client.get(f'/api/v1/carreras/{carrera_ajena.id}')
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_estadisticas_mensual(self):
        Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta 1', distancia_km='5.000',
            duracion_seg=1500, iniciada_en=timezone.now(),
        )
        mes = timezone.now().strftime('%Y-%m')
        respuesta = self.client.get(f'/api/v1/estadisticas/mensual?mes={mes}')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['conteo_carreras'], 1)
