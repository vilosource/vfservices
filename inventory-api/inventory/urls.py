from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('private/', views.private, name='private'),
    path('test-rbac/', views.test_rbac, name='test_rbac'),
    path('inventory-manager/', views.inventory_manager_only, name='inventory_manager_only'),
    path('menus/<str:menu_name>/', views.get_menu, name='get_menu'),
]
