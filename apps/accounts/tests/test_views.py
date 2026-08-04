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
        self.assertIn('pendiente', str(respuesta.data).lower())

    def test_login_correo_inexistente_es_especifico(self):
        respuesta = self.client.post(reverse('auth-login'), {
            'correo': 'no-existe@example.com',
            'password': 'lo-que-sea',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('no existe', str(respuesta.data).lower())

    def test_login_password_incorrecto_es_especifico(self):
        Usuario.objects.create_user(
            correo='activo2@example.com', password='clave-correcta-123',
            nombre_completo='Activo2', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        respuesta = self.client.post(reverse('auth-login'), {
            'correo': 'activo2@example.com',
            'password': 'clave-incorrecta',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('incorrecta', str(respuesta.data).lower())

    def test_olvide_password_correo_inexistente_es_especifico(self):
        respuesta = self.client.post(reverse('auth-olvide-password'), {'correo': 'no-existe@example.com'})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no existe', str(respuesta.data).lower())


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

    @patch('apps.accounts.views.validar_google_id_token')
    def test_google_rechaza_si_ya_existe_cuenta_local(self, mock_validar):
        Usuario.objects.create_user(
            correo='ya.registrado@example.com', password='clave-segura-123',
            nombre_completo='Ya Registrado', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        mock_validar.return_value = {
            'sub': 'google-uid-999',
            'email': 'ya.registrado@example.com',
            'name': 'Ya Registrado',
        }
        google_url = reverse('auth-google')
        respuesta = self.client.post(google_url, {'id_token': 'token-falso'})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        usuario = Usuario.objects.get(correo='ya.registrado@example.com')
        self.assertEqual(usuario.provider, Usuario.PROVIDER_LOCAL)
        self.assertIsNone(usuario.google_id)


class PasswordGoogleRestrictionTests(APITestCase):
    def setUp(self):
        self.usuario_google = Usuario.objects.create(
            correo='google@example.com', nombre_completo='Google User', pais='HN',
            provider=Usuario.PROVIDER_GOOGLE, google_id='google-uid-1', estado=Usuario.ESTADO_ACTIVO,
        )
        self.usuario_google.set_unusable_password()
        self.usuario_google.save()

    def test_olvide_password_rechaza_cuenta_google(self):
        respuesta = self.client.post(reverse('auth-olvide-password'), {'correo': 'google@example.com'})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_password_rechaza_cuenta_google(self):
        self.client.force_authenticate(user=self.usuario_google)
        respuesta = self.client.post(reverse('usuario-me-password'), {
            'password_actual': 'lo-que-sea',
            'nueva_password': 'clave-nueva-segura-123',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class CambiarPasswordViewTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='local@example.com', password='clave-vieja-123',
            nombre_completo='Local', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.client.force_authenticate(user=self.usuario)

    def test_cambiar_password_exitoso(self):
        respuesta = self.client.post(reverse('usuario-me-password'), {
            'password_actual': 'clave-vieja-123',
            'nueva_password': 'clave-nueva-segura-456',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave-nueva-segura-456'))

    def test_cambiar_password_actual_incorrecto(self):
        respuesta = self.client.post(reverse('usuario-me-password'), {
            'password_actual': 'password-incorrecto',
            'nueva_password': 'clave-nueva-segura-456',
        })
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave-vieja-123'))


class UsuarioMeMetaRachaSemanalTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='racha@example.com', password='clave-segura-123',
            nombre_completo='Racha', pais='HN', estado=Usuario.ESTADO_ACTIVO,
        )
        self.client.force_authenticate(user=self.usuario)

    def test_actualizar_meta_racha_semanal(self):
        respuesta = self.client.patch(reverse('usuario-me'), {'meta_racha_semanal': 4})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['meta_racha_semanal'], 4)

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.meta_racha_semanal, 4)

    def test_rechaza_meta_racha_semanal_fuera_de_rango(self):
        respuesta = self.client.patch(reverse('usuario-me'), {'meta_racha_semanal': 8})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


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
