from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CodigoOTP, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    ordering = ['-creado_en']
    list_display = ['correo', 'nombre_completo', 'pais', 'provider', 'estado', 'is_staff']
    list_filter = ['provider', 'estado', 'pais', 'is_staff']
    search_fields = ['correo', 'nombre_completo']
    readonly_fields = ['creado_en', 'last_login']

    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        ('Informacion personal', {'fields': ('nombre_completo', 'pais', 'foto_url', 'peso_kg', 'meta_racha_semanal')}),
        ('Autenticacion', {'fields': ('provider', 'google_id', 'estado')}),
        ('Permisos', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'creado_en')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo', 'nombre_completo', 'pais', 'password1', 'password2'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(CodigoOTP)
class CodigoOTPAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'usado', 'intentos', 'expira_en', 'creado_en']
    list_filter = ['tipo', 'usado']
    search_fields = ['usuario__correo']
    readonly_fields = ['codigo', 'creado_en']
