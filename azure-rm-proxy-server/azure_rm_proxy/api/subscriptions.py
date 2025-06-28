from fastapi import Depends, APIRouter, Query
from typing import Dict
from ..app.dependencies import get_azure_service
from ..core.models import SubscriptionModel
from ..core.azure_service import AzureResourceService
from ..auth import get_current_user_with_roles
from ..rbac import check_read_permission, check_write_permission, check_admin_permission

router = APIRouter(tags=["Subscriptions"], prefix="/api/subscriptions")


@router.get("/", response_model=list[SubscriptionModel])
async def list_subscriptions(
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
    current_user: Dict = Depends(check_read_permission),
):
    return await azure_service.get_subscriptions(refresh_cache=refresh_cache)
