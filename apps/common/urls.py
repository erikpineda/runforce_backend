from django.urls import path

from . import views

urlpatterns = [
    path('paises', views.PaisesListView.as_view(), name='paises-list'),
]
