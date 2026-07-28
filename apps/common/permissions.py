from rest_framework.permissions import BasePermission


class EsPropietario(BasePermission):
    """Permite acceso solo al dueno del objeto (campo `usuario`)."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'usuario_id', None) == request.user.id
