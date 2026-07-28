from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.runs.models import Carrera


class CarreraModelTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='runner@example.com', password='clave-segura-123',
            nombre_completo='Runner', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )

    def test_calcula_ritmo_y_calorias_sin_peso(self):
        carrera = Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta matutina', distancia_km='5.000',
            duracion_seg=1500, iniciada_en=timezone.now(),
        )
        self.assertEqual(carrera.ritmo_seg_km, 300)
        self.assertEqual(carrera.calorias, 300)

    def test_calcula_calorias_con_peso(self):
        self.usuario.peso_kg = '70.00'
        self.usuario.save()
        carrera = Carrera.objects.create(
            usuario=self.usuario, titulo='Ruta con peso', distancia_km='10.000',
            duracion_seg=3000, iniciada_en=timezone.now(),
        )
        self.assertEqual(carrera.calorias, round(70 * 10 * 1.036))
