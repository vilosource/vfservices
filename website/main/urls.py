"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from . import views 

urlpatterns = [
    path("admin/", admin.site.urls),
    path("webdev/base.html", views.base, name="base"),
    path("webdev/index.html", views.index, name="index"),
    path("webdev/auth.html", views.auth, name="index"),
    path("webdev/template_viewer/", views.template_viewer, name="template_viewer"),
    path("webdev/template_viewer/<str:template_name>/", views.template_viewer, name="template_viewer"),
    path("", include("webapp.urls")),
]
