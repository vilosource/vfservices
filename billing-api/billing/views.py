from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def private(request):
    return Response({"user": request.user.username})


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    return Response({
        "message": "Welcome to the Billing API",
        "endpoints": {
            "health": "/health/",
            "private": "/private/ (requires authentication)",
        }
    })
