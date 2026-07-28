from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CodigoOTP, Usuario


class RegistroYLoginFlowTests(APITestCase):
    def test_registro_verificacion_y_login(self):
        registro_url = reverse('auth-registro')
        respuesta = self.client.post(registro_url, {
            'nombre_completo': 'Runner Uno',
            'correo': 'runner@example.com',
            'password': 'clave-segura-123',
            'pais': 'HN',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        usuario = Usuario.objects.get(correo='runner@example.com')
        self.assertEqual(usuario.estado, Usuario.ESTADO_PENDIENTE)

        codigo_otp = CodigoOTP.objects.get(usuario=usuario, tipo=CodigoOTP.TIPO_REGISTRO)

        verificar_url = reverse('auth-verificar-otp')
        respuesta = self.client.post(verificar_url, {
            'correo': 'runner@example.com',
            'codigo': codigo_otp.codigo,
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)

        usuario.refresh_from_db()
        self.assertEqual(usuario.estado, Usuario.ESTADO_ACTIVO)

        login_url = reverse('auth-login')
        respuesta = self.client.post(login_url, {
            'correo': 'runner@example.com',
            'password': 'clave-segura-123',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)

    def test_registro_rechaza_pais_invalido(self):
        registro_url = reverse('auth-registro')
        respuesta = self.client.post(registro_url, {
            'nombre_completo': 'Runner Invalido',
            'correo': 'invalido@example.com',
            'password': 'clave-segura-123',
            'pais': 'XX',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Usuario.objects.filter(correo='invalido@example.com').exists())

    def test_login_pendiente_es_rechazado(self):
        Usuario.objects.create_user(
            correo='pendiente@example.com', password='clave-segura-123',
            nombre_completo='Pendiente', pais='HN',
        )
        login_url = reverse('auth-login')
        respuesta = self.client.post(login_url, {
            'correo': 'pendiente@example.com',
            'password': 'clave-segura-123',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)


class GoogleAuthTests(APITestCase):
    @patch('apps.accounts.views.validar_google_id_token')
    def test_login_google_crea_usuario_activo(self, mock_validar):
        mock_validar.return_value = {
            'sub': 'google-uid-123',
            'email': 'google.user@example.com',
            'name': 'Google User',
            'picture': 'https://example.com/foto.jpg',
        }
        google_url = reverse('auth-google')
        respuesta = self.client.post(google_url, {'id_token': 'token-falso'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)

        usuario = Usuario.objects.get(correo='google.user@example.com')
        self.assertEqual(usuario.provider, Usuario.PROVIDER_GOOGLE)
        self.assertEqual(usuario.estado, Usuario.ESTADO_ACTIVO)


class RefreshTokenTests(APITestCase):
    def test_refresh_token_entrega_nuevo_access(self):
        usuario = Usuario.objects.create_user(
            correo='activo@example.com', password='clave-segura-123',
            nombre_completo='Activo', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        login_url = reverse('auth-login')
        login_resp = self.client.post(login_url, {
            'correo': 'activo@example.com',
            'password': 'clave-segura-123',
        })
        refresh = login_resp.data['refresh']

        refresh_url = reverse('auth-token-refresh')
        respuesta = self.client.post(refresh_url, {'refresh': refresh})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)
