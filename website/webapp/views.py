from django.shortcuts import render


def home(request):
    """Render the demo home page."""
    return render(request, "webapp/index.html")
