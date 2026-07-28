from django.urls import path

from . import views

urlpatterns = [
    path('corredores', views.CorredoresListView.as_view(), name='corredores-list'),
    path('amigos', views.AmigosListCreateView.as_view(), name='amigos-list-create'),
    path('ranking', views.RankingView.as_view(), name='ranking'),
]
