from fastapi import APIRouter, status, Depends, HTTPException
from src.domain.interfaces.user.user_repositiry import IUserRepository
from src.dependencies import get_user_repository
from src.domain.entity.users.user import User
import logging

router = APIRouter(prefix='/api/user')
logger = logging.getLogger(__name__)

@router.get('/{user_id}', response_model=User)
async def get_user(
    user_id: int,
    user_repo: IUserRepository = Depends(get_user_repository)
):
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )