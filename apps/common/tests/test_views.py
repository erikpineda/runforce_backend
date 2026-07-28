from rest_framework import status
from rest_framework.test import APITestCase


class PaisesListViewTests(APITestCase):
    def test_lista_paises_sin_autenticacion(self):
        respuesta = self.client.get('/api/v1/paises')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(respuesta.data), 10)
        codigos = {fila['codigo'] for fila in respuesta.data}
        self.assertIn('HN', codigos)

    def test_no_esta_paginado(self):
        respuesta = self.client.get('/api/v1/paises')
        self.assertIsInstance(respuesta.data, list)
