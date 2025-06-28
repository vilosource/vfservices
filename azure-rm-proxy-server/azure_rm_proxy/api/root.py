from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_root():
    """
    Root endpoint - redirects to /api/.
    """
    return {"message": "Azure RM Proxy Server. Visit /api/ for API information or /docs for documentation."}


@router.get("/api/")
def get_api_info():
    """
    API root endpoint with project information.
    """
    return {
        "name": "Azure RM Proxy API",
        "version": "1.0.0",
        "description": "REST API proxy for Azure Resource Manager",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/ping"
    }
