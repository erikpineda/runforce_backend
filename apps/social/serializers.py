from django.contrib.auth import get_user_model
from rest_framework import serializers

Usuario = get_user_model()


class CorredorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre_completo', 'pais', 'foto_url']


class AgregarAmigoSerializer(serializers.Serializer):
    amigo_id = serializers.IntegerField()

    def validate_amigo_id(self, value):
        if not Usuario.objects.filter(id=value, estado=Usuario.ESTADO_ACTIVO).exists():
            raise serializers.ValidationError('El usuario indicado no existe.')
        return value


class RankingItemSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()
    nombre_completo = serializers.CharField()
    pais = serializers.CharField()
    km_totales = serializers.DecimalField(max_digits=10, decimal_places=3)
