from django.urls import path

from . import views

urlpatterns = [
    path('carreras', views.CarreraListCreateView.as_view(), name='carrera-list-create'),
    path('carreras/<int:pk>', views.CarreraDetailView.as_view(), name='carrera-detail'),
    path('estadisticas/mensual', views.EstadisticasMensualView.as_view(), name='estadisticas-mensual'),
    path('estadisticas/comparativo', views.EstadisticasComparativoView.as_view(), name='estadisticas-comparativo'),
]
