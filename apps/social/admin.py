from django.contrib import admin

from .models import Amistad


@admin.register(Amistad)
class AmistadAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'amigo', 'estado', 'creado_en']
    list_filter = ['estado']
    search_fields = ['usuario__correo', 'amigo__correo']
