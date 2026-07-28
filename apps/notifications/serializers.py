from rest_framework import serializers

from .models import Dispositivo, Notificacion


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ['id', 'onesignal_player_id', 'plataforma']
        read_only_fields = ['id']


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'tipo', 'mensaje', 'leido', 'creado_en']
        read_only_fields = ['id', 'tipo', 'mensaje', 'creado_en']
