from django.urls import path
from . import views

urlpatterns = [

    path('private/', views.private, name='private'),
    path('', views.home, name='home'),
]
