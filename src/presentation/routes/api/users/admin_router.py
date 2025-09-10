import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.domain.entity.users.user import User, Role
from src.use_cases.repository.users_usecases import AdminUseCase
from src.dependencies import get_current_user, get_admin_use_case
from src.infrastructure.repository.schemas.user_orm import AdminActionsSchema
from src.domain.entity.users.admin.admin_entity import Admin as AdminEntity

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

def is_admin(user: User = Depends(get_current_user)) -> AdminEntity:
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: User is not an admin"
        )
    return user


@router.get("/me", response_model=AdminEntity)
async def get_my_admin_profile(
    admin_user: AdminEntity = Depends(is_admin),
    admin_use_case: AdminUseCase = Depends(get_admin_use_case)
):
    try:
        admin_profile = await admin_use_case.get_admin_profile(admin_user.id)
        if not admin_profile:
            raise HTTPException(status_code=404, detail="Admin profile not found")
        return admin_profile
    except Exception as e:
        logger.error(f"Error getting admin profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/users", response_model=List[User])
async def get_all_users(
    page: int = 1,
    page_size: int = 10,
    admin_user: AdminEntity = Depends(is_admin),
    admin_use_case: AdminUseCase = Depends(get_admin_use_case)
):
    try:
        users = await admin_use_case.get_all_users(page=page, page_size=page_size)
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/user-actions")
async def user_actions(
    request: AdminActionsSchema,
    admin_user: AdminEntity = Depends(is_admin),
    admin_use_case: AdminUseCase = Depends(get_admin_use_case)
):
    try:
        result = False
        if request.action == "block":
            result = await admin_use_case.block_user(request.user_id, request.reason)
            if not result:
                raise HTTPException(status_code=400, detail="User already blocked or action failed")
        elif request.action == "unblock":
            result = await admin_use_case.unblock_user(request.user_id)
            if not result:
                raise HTTPException(status_code=400, detail="User is not blocked or action failed")
        elif request.action == "delete":
            result = await admin_use_case.delete_user(request.user_id)
            if not result:
                raise HTTPException(status_code=404, detail="User not found or action failed")
        else:
            raise HTTPException(status_code=400, detail="Invalid action specified")

        return {"message": f"User {request.user_id} successfully {request.action}ed."}

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error performing admin action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/statistics")
async def get_statistics(
    admin_user: AdminEntity = Depends(is_admin),
    admin_use_case: AdminUseCase = Depends(get_admin_use_case)
):
    try:
        statistics = await admin_use_case.get_statisctics()
        return statistics
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{admin_id}", response_model=AdminEntity)
async def get_admin_by_id(
    admin_id: int,
    admin_user: AdminEntity = Depends(is_admin),
    admin_use_case: AdminUseCase = Depends(get_admin_use_case)
):
    try:
        admin = await admin_use_case.get_admin_profile(admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin
    except Exception as e:
        logger.error(f"Error getting admin: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
