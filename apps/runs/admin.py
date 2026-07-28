from django.contrib import admin

from .models import Carrera


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'distancia_km', 'duracion_seg', 'ritmo_seg_km', 'calorias', 'iniciada_en']
    list_filter = ['iniciada_en']
    search_fields = ['titulo', 'usuario__correo']
    readonly_fields = ['ritmo_seg_km', 'calorias', 'creado_en']
