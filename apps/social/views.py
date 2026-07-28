from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Amistad
from .serializers import AgregarAmigoSerializer, CorredorSerializer, RankingItemSerializer
from .services import agregar_amigo, construir_ranking

Usuario = get_user_model()

TAG_SOCIAL = 'Social'


@extend_schema_view(
    get=extend_schema(
        tags=[TAG_SOCIAL],
        summary='Buscar corredores',
        description='Lista corredores activos (excluye al usuario autenticado), filtrable por pais y texto libre.',
        parameters=[
            OpenApiParameter('pais', str, description='Codigo/nombre de pais, ej. HN'),
            OpenApiParameter('q', str, description='Busca en nombre_completo y correo'),
        ],
    )
)
class CorredoresListView(generics.ListAPIView):
    serializer_class = CorredorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Usuario.objects.filter(estado=Usuario.ESTADO_ACTIVO).exclude(id=self.request.user.id)

        pais = self.request.query_params.get('pais')
        if pais:
            queryset = queryset.filter(pais=pais)

        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(Q(nombre_completo__icontains=q) | Q(correo__icontains=q))

        return queryset


class AmigosListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=[TAG_SOCIAL], summary='Listar mis amigos', responses={200: CorredorSerializer(many=True)})
    def get(self, request):
        amigos_ids = Amistad.objects.filter(
            usuario=request.user, estado=Amistad.ESTADO_ACEPTADA
        ).values_list('amigo_id', flat=True)
        amigos = Usuario.objects.filter(id__in=amigos_ids)
        return Response(CorredorSerializer(amigos, many=True).data)

    @extend_schema(
        tags=[TAG_SOCIAL],
        summary='Agregar amigo',
        description='Crea la amistad de forma reciproca y auto-aceptada; dispara una notificacion al agregado.',
        request=AgregarAmigoSerializer,
        responses={201: CorredorSerializer},
    )
    def post(self, request):
        serializer = AgregarAmigoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amigo_id = serializer.validated_data['amigo_id']

        if amigo_id == request.user.id:
            raise ValidationError('No puedes agregarte a ti mismo como amigo.')

        amigo = Usuario.objects.get(id=amigo_id)
        agregar_amigo(request.user, amigo)

        from apps.notifications.services import notificar_solicitud_amistad
        notificar_solicitud_amistad(origen=request.user, destino=amigo)

        return Response(CorredorSerializer(amigo).data, status=status.HTTP_201_CREATED)


class RankingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_SOCIAL],
        summary='Ranking',
        description=(
            'Sin `pais`: ranking entre el usuario y sus amigos. Con `pais`: ranking entre todos los '
            'corredores activos de ese pais, en ambos casos ordenado por km acumulados en el periodo.'
        ),
        parameters=[
            OpenApiParameter('pais', str, description='Si se indica, ignora la lista de amigos'),
            OpenApiParameter('periodo', str, description='`mes` (default) o `semana`'),
        ],
        responses={200: RankingItemSerializer(many=True)},
    )
    def get(self, request):
        pais = request.query_params.get('pais')
        periodo = request.query_params.get('periodo', 'mes')
        if periodo not in ('mes', 'semana'):
            raise ValidationError('El parametro `periodo` debe ser `mes` o `semana`.')

        ranking = construir_ranking(request.user, pais=pais, periodo=periodo)
        return Response(RankingItemSerializer(ranking, many=True).data)
