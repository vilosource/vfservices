from django.urls import path
from . import views
from rest_framework.views import APIView

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
]
