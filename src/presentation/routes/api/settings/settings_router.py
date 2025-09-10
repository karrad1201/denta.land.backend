from fastapi import APIRouter, status, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from src.infrastructure.repository.schemas.user_orm import Role
from src.use_cases.repository.users_usecases import SetSettingsUseCase
from jose.exceptions import JWSError
from src.dependencies import get_settings_use_case
from typing import Optional, List, Dict, Any
import logging

router = APIRouter(prefix='/api/settings')
logger = logging.getLogger(__name__)


class UserSettingsUpdate(BaseModel):
    nickname: Optional[str] = Field(None, pattern='^[a-zA-Z0-9_]+$', min_length=4, max_length=20)
    name: Optional[str] = Field(None, min_length=2, max_length=30)
    photo_path: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = Field(None, min_length=5, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=30)
    city: Optional[str] = None
    specifications: Optional[List[str]] = None
    qualification: Optional[str] = None
    locations: Optional[List[str]] = None
    admin_role: Optional[str] = None
    is_superadmin: Optional[bool] = None


@router.put('', response_model=dict, status_code=status.HTTP_200_OK)
async def update_user_settings(
        request: Request,
        update_data: UserSettingsUpdate,
        authorization: str = Header(..., alias="Authorization"),
        use_case: SetSettingsUseCase = Depends(get_settings_use_case)
):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
        jwt_token = authorization.split(" ")[1]

        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)

        await use_case.execute(update_dict, jwt_token)

        return {"message": "User settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Settings update error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except JWSError as e:
        logger.error(f"Token error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )