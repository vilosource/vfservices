from django.shortcuts import render
from django.conf import settings

# These are views for rendering templates in a Django application for testing and development purposes. 


def index(request):
    """
    Render the index template.
    """
    return render(request, "index.html")




def base(request):
    """
    Render the base template.
    """
    return render(request, "base.html" )



def auth(request):
    """
    Render the auth template.
    """
    return render(request, "auth.html")

def template_viewer(request, template_name=None):
    """
    A utility view to render a template for testing purposes.
    This view can be used to render any template by specifying the template name in the request.
    This is useful for developers to quickly view and test templates without needing to set up a full view logic.
    Usage:

    The url /template_viewer/<template_name>/ will render the specified template.
    Example:
    /template_viewer/template_name.html will render template_name.html.
    """
    # This view does not require any specific logic, it simply renders the template_viewer.html.
    if template_name is None:

        #get a list of all templates in the templates directory
        template_dir = settings.TEMPLATES[0]['DIRS'][0]
        import os
        templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
        # Render the template viewer with a list of available templates
        return render(request, "template_viewer.html", {"templates": templates})
    
    else:
        # Ensure the template name is safe to render
        template_name = template_name.strip().replace("..", "").replace("/", "").replace("\\", "")

    return render(request, template_name)