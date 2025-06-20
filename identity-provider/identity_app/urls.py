from django.urls import path, include
from . import views
from rest_framework.views import APIView

urlpatterns = [
    path('', views.index_view, name='index'),  # Root URL redirects to login
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('api/', views.APIInfoView.as_view(), name='api_info'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/status/', views.api_status, name='api_status'),
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/services/register/', views.ServiceRegisterView.as_view(), name='service_register'),
    path('api/refresh-user-cache/', views.RefreshUserCacheView.as_view(), name='refresh_user_cache'),
    
    # Admin API endpoints
    path('api/admin/', include('identity_app.admin_urls')),
]
