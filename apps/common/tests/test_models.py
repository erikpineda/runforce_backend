from django.test import TestCase

from apps.common.models import Pais


class PaisModelTests(TestCase):
    """Las migraciones ya siembran el catalogo real; se usa un codigo `ZZ`
    ficticio para no chocar con esos datos."""

    def test_str_incluye_codigo_y_nombre(self):
        pais = Pais.objects.create(codigo='ZZ', nombre='Zetalandia')
        self.assertEqual(str(pais), 'Zetalandia (ZZ)')

    def test_codigo_es_unico(self):
        Pais.objects.create(codigo='ZZ', nombre='Zetalandia')
        with self.assertRaises(Exception):
            Pais.objects.create(codigo='ZZ', nombre='Duplicado')

    def test_seed_de_migracion_incluye_centroamerica(self):
        codigos = set(Pais.objects.values_list('codigo', flat=True))
        for esperado in ('HN', 'GT', 'SV', 'NI', 'CR', 'PA', 'BZ'):
            self.assertIn(esperado, codigos)
