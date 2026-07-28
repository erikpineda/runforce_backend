from datetime import datetime

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import EsPropietario

from .models import Carrera
from .serializers import CarreraSerializer, EstadisticasComparativoSerializer, ResumenPeriodoSerializer
from .services import mes_actual_y_anterior, rango_mes, resumen_periodo, semana_actual_y_anterior

TAG_CARRERAS = 'Carreras'
TAG_ESTADISTICAS = 'Estadisticas'


@extend_schema_view(
    get=extend_schema(
        tags=[TAG_CARRERAS],
        summary='Listar mis carreras',
        description='Historial paginado de carreras del usuario autenticado, filtrable por rango de fechas.',
        parameters=[
            OpenApiParameter('desde', str, description='ISO 8601, filtra `iniciada_en >= desde`'),
            OpenApiParameter('hasta', str, description='ISO 8601, filtra `iniciada_en <= hasta`'),
        ],
    ),
    post=extend_schema(
        tags=[TAG_CARRERAS],
        summary='Registrar una carrera',
        description='`ritmo_seg_km` y `calorias` se calculan automaticamente en el servidor.',
    ),
)
class CarreraListCreateView(generics.ListCreateAPIView):
    serializer_class = CarreraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Carrera.objects.filter(usuario=self.request.user)

        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        if desde:
            queryset = queryset.filter(iniciada_en__gte=desde)
        if hasta:
            queryset = queryset.filter(iniciada_en__lte=hasta)

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


@extend_schema_view(
    get=extend_schema(tags=[TAG_CARRERAS], summary='Detalle de una carrera'),
    put=extend_schema(tags=[TAG_CARRERAS], summary='Editar una carrera (reemplazo completo)'),
    patch=extend_schema(tags=[TAG_CARRERAS], summary='Editar una carrera (parcial)'),
    delete=extend_schema(tags=[TAG_CARRERAS], summary='Eliminar una carrera'),
)
class CarreraDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarreraSerializer
    permission_classes = [IsAuthenticated, EsPropietario]

    def get_queryset(self):
        return Carrera.objects.filter(usuario=self.request.user)


class EstadisticasMensualView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_ESTADISTICAS],
        summary='Estadisticas de un mes',
        description='Km totales, calorias y conteo de carreras del mes indicado (o el mes actual si se omite).',
        parameters=[OpenApiParameter('mes', str, description='Formato YYYY-MM, ej. 2026-07')],
        responses={200: ResumenPeriodoSerializer},
    )
    def get(self, request):
        mes_param = request.query_params.get('mes')
        if mes_param:
            try:
                fecha = datetime.strptime(mes_param, '%Y-%m')
            except ValueError:
                raise ValidationError('El parametro `mes` debe tener el formato YYYY-MM.')
            fecha = timezone.make_aware(fecha)
        else:
            fecha = timezone.now()

        inicio, fin = rango_mes(fecha)
        resumen = resumen_periodo(Carrera.objects, request.user, inicio, fin)
        return Response(ResumenPeriodoSerializer(resumen).data)


class EstadisticasComparativoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_ESTADISTICAS],
        summary='Comparativo semana/mes actual vs. anterior',
        responses={200: EstadisticasComparativoSerializer},
    )
    def get(self, request):
        (inicio_semana_actual, fin_semana_actual), (inicio_semana_anterior, fin_semana_anterior) = (
            semana_actual_y_anterior()
        )
        (inicio_mes_actual, fin_mes_actual), (inicio_mes_anterior, fin_mes_anterior) = mes_actual_y_anterior()

        datos = {
            'semana_actual': resumen_periodo(Carrera.objects, request.user, inicio_semana_actual, fin_semana_actual),
            'semana_anterior': resumen_periodo(
                Carrera.objects, request.user, inicio_semana_anterior, fin_semana_anterior
            ),
            'mes_actual': resumen_periodo(Carrera.objects, request.user, inicio_mes_actual, fin_mes_actual),
            'mes_anterior': resumen_periodo(Carrera.objects, request.user, inicio_mes_anterior, fin_mes_anterior),
        }
        return Response(EstadisticasComparativoSerializer(datos).data)
