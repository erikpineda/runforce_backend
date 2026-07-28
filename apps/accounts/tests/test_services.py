from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import CodigoOTP, Usuario
from apps.accounts.services import generar_y_enviar_otp, validar_otp


class OTPServiceTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            correo='runner@example.com', password='clave-segura-123', nombre_completo='Runner', pais='HN'
        )

    def test_generar_otp_envia_correo(self):
        codigo_otp = generar_y_enviar_otp(self.usuario, CodigoOTP.TIPO_REGISTRO)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(codigo_otp.codigo, mail.outbox[0].body)

    def test_validar_otp_correcto_lo_marca_usado(self):
        codigo_otp = generar_y_enviar_otp(self.usuario, CodigoOTP.TIPO_REGISTRO)
        validar_otp(self.usuario, codigo_otp.codigo, CodigoOTP.TIPO_REGISTRO)
        codigo_otp.refresh_from_db()
        self.assertTrue(codigo_otp.usado)

    def test_validar_otp_incorrecto_incrementa_intentos(self):
        generar_y_enviar_otp(self.usuario, CodigoOTP.TIPO_REGISTRO)
        with self.assertRaises(ValidationError):
            validar_otp(self.usuario, '000000', CodigoOTP.TIPO_REGISTRO)
        codigo_otp = CodigoOTP.objects.get(usuario=self.usuario, usado=False)
        self.assertEqual(codigo_otp.intentos, 1)

    def test_validar_otp_expirado_falla(self):
        codigo_otp = generar_y_enviar_otp(self.usuario, CodigoOTP.TIPO_REGISTRO)
        codigo_otp.expira_en = timezone.now() - timezone.timedelta(minutes=1)
        codigo_otp.save()
        with self.assertRaises(ValidationError):
            validar_otp(self.usuario, codigo_otp.codigo, CodigoOTP.TIPO_REGISTRO)
