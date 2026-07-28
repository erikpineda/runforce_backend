from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dispositivo, Notificacion
from .serializers import DispositivoSerializer, NotificacionSerializer

TAG_NOTIFICACIONES = 'Notificaciones'


class DispositivoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_NOTIFICACIONES],
        summary='Registrar dispositivo para push',
        description='Registra o actualiza el player id de OneSignal del dispositivo Android del usuario.',
        request=DispositivoSerializer,
        responses={201: DispositivoSerializer},
    )
    def post(self, request):
        serializer = DispositivoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispositivo, _creado = Dispositivo.objects.update_or_create(
            usuario=request.user,
            onesignal_player_id=serializer.validated_data['onesignal_player_id'],
            defaults={'plataforma': serializer.validated_data.get('plataforma', Dispositivo.PLATAFORMA_ANDROID)},
        )
        return Response(DispositivoSerializer(dispositivo).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(tags=[TAG_NOTIFICACIONES], summary='Listar mis notificaciones'),
)
class NotificacionesListView(generics.ListAPIView):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)


class NotificacionLeidoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=[TAG_NOTIFICACIONES],
        summary='Marcar notificacion como leida',
        request=None,
        responses={200: NotificacionSerializer},
    )
    def put(self, request, pk):
        notificacion = generics.get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notificacion.leido = True
        notificacion.save(update_fields=['leido'])
        return Response(NotificacionSerializer(notificacion).data)
