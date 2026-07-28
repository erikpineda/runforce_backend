from django.urls import path

from . import views

urlpatterns = [
    path('dispositivos', views.DispositivoView.as_view(), name='dispositivo-registrar'),
    path('notificaciones', views.NotificacionesListView.as_view(), name='notificaciones-list'),
    path('notificaciones/<int:pk>/leido', views.NotificacionLeidoView.as_view(), name='notificacion-leido'),
]
