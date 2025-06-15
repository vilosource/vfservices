from django.urls import path
from . import views
from rest_framework.views import APIView

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('api/', views.APIInfoView.as_view(), name='api_info'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/status/', views.api_status, name='api_status'),
    path('api/profile/', views.api_profile, name='api_profile'),
]
