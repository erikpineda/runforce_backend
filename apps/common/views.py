from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser


class DocsAccessMixin:
    """
    En development (DEBUG=True) la documentacion queda publica.
    En production/testing (DEBUG=False) solo un usuario staff puede verla,
    autenticado por JWT o por la sesion de /admin/ (para poder abrir
    /api/docs/ desde el navegador sin tener que generar un token).
    """

    def get_permissions(self):
        if settings.DEBUG:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_authenticators(self):
        authenticators = super().get_authenticators()
        authenticators.append(SessionAuthentication())
        return authenticators


class DocsSchemaView(DocsAccessMixin, SpectacularAPIView):
    pass


class DocsSwaggerView(DocsAccessMixin, SpectacularSwaggerView):
    pass
