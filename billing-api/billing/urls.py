from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('health/', views.health, name='health'),
    path('private/', views.private, name='private'),
    path('test-rbac/', views.test_rbac, name='test_rbac'),
    path('billing-admin/', views.billing_admin_only, name='billing_admin_only'),
    path('customer-manager/', views.customer_manager_only, name='customer_manager_only'),
    path('invoice-manager/', views.invoice_manager_only, name='invoice_manager_only'),
]
