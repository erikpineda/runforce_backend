from rest_framework import serializers

from .models import Carrera


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = [
            'id', 'titulo', 'distancia_km', 'duracion_seg', 'ritmo_seg_km',
            'calorias', 'ruta_geojson', 'elevacion_m', 'iniciada_en', 'creado_en',
        ]
        read_only_fields = ['id', 'ritmo_seg_km', 'calorias', 'creado_en']


class ResumenPeriodoSerializer(serializers.Serializer):
    km_totales = serializers.DecimalField(max_digits=10, decimal_places=3)
    calorias_totales = serializers.IntegerField()
    conteo_carreras = serializers.IntegerField()


class EstadisticasComparativoSerializer(serializers.Serializer):
    semana_actual = ResumenPeriodoSerializer()
    semana_anterior = ResumenPeriodoSerializer()
    mes_actual = ResumenPeriodoSerializer()
    mes_anterior = ResumenPeriodoSerializer()
