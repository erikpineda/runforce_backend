from django.contrib import admin

from .models import Dispositivo, Notificacion


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plataforma', 'onesignal_player_id']
    search_fields = ['usuario__correo', 'onesignal_player_id']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'leido', 'creado_en']
    list_filter = ['tipo', 'leido']
    search_fields = ['usuario__correo']
