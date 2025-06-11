import datetime
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.jwt_auth import utils


def login_user(request):
    """Render login form or authenticate user and set JWT cookie."""
    if request.method == "GET":
        return render(request, "identity_app/login.html")

    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(username=username, password=password)
    if user is None:
        return HttpResponseForbidden("Invalid login")

    payload = {
        "username": user.username,
        "email": user.email,
        "iat": datetime.datetime.utcnow(),
    }
    token = utils.encode_jwt(payload)

    redirect_url = request.GET.get("redirect_uri", settings.DEFAULT_REDIRECT_URL)
    response = HttpResponseRedirect(redirect_url)
    response.set_cookie(
        "jwt",
        token,
        domain=settings.SSO_COOKIE_DOMAIN,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=3600,
    )
    return response


def logout_user(request):
    """Clear the JWT cookie across the domain."""
    response = HttpResponseRedirect(settings.DEFAULT_REDIRECT_URL)
    response.delete_cookie("jwt", domain=settings.SSO_COOKIE_DOMAIN)
    return response


class LoginAPIView(APIView):
    """API endpoint to obtain JWT via username and password."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = {
            "username": user.username,
            "email": user.email,
            "iat": datetime.datetime.utcnow(),
        }
        token = utils.encode_jwt(payload)
        return Response({"token": token})
