from django.urls import path
from . import views

urlpatterns = [
    path('private/', views.private, name='private'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.home, name='home'),
]
