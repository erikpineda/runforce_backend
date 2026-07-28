from django.test import TestCase

from apps.accounts.models import Usuario


class UsuarioModelTests(TestCase):
    def test_create_user_queda_pendiente_por_defecto(self):
        usuario = Usuario.objects.create_user(
            correo='runner@example.com', password='clave-segura-123', nombre_completo='Runner', pais='HN'
        )
        self.assertEqual(usuario.estado, Usuario.ESTADO_PENDIENTE)
        self.assertFalse(usuario.is_active)
        self.assertTrue(usuario.check_password('clave-segura-123'))

    def test_usuario_activo_is_active_true(self):
        usuario = Usuario.objects.create_user(
            correo='runner2@example.com', password='clave-segura-123', nombre_completo='Runner2', pais='HN'
        )
        usuario.estado = Usuario.ESTADO_ACTIVO
        usuario.save()
        self.assertTrue(usuario.is_active)

    def test_create_superuser_queda_activo_y_staff(self):
        admin = Usuario.objects.create_superuser(correo='admin@example.com', password='clave-super-123')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
