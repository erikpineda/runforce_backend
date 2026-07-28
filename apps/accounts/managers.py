from django.contrib.auth.base_user import BaseUserManager


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El usuario debe tener un correo electronico.')
        correo = self.normalize_email(correo)
        usuario = self.model(correo=correo, **extra_fields)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('nombre_completo', 'Administrador')
        extra_fields.setdefault('pais', 'HN')
        extra_fields.setdefault('estado', 'activo')
        extra_fields.setdefault('is_staff', True)

        usuario = self.create_user(correo, password, **extra_fields)
        usuario.is_superuser = True
        usuario.save(using=self._db)
        return usuario
