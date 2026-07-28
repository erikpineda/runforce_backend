from django.conf import settings
from drf_spectacular.utils import extend_schema_view, extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import Pais
from .serializers import PaisSerializer


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


@extend_schema_view(
    get=extend_schema(
        tags=['Comun'],
        summary='Listar paises',
        description='Catalogo de paises (codigo ISO 3166-1 alpha-2 + nombre) para poblar un selector en el cliente.',
    )
)
class PaisesListView(generics.ListAPIView):
    """Catalogo de paises para poblar un selector en el cliente (sin login)."""
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    permission_classes = [AllowAny]
    pagination_class = None
