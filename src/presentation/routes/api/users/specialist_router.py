from fastapi import APIRouter, status, Depends, HTTPException, Header
from src.dependencies import get_specialist_repository, get_user_repository
from src.domain.entity.users.specialist.specialist import Specialist
from src.infrastructure.repository.user.postgres_specialist_repo import PostgresSpecialistRepo
from src.infrastructure.repository.user.postgres_user_repo import PostgresUserRepo

router = APIRouter(prefix='/api/specialists', tags=['Specialists'])

@router.get('/me', response_model=Specialist)
async def get_my_spec(
    org_repo: PostgresSpecialistRepo = Depends(get_specialist_repository),
    authorization: str = Header(..., alias="Authorization"),
    user_repo: PostgresUserRepo = Depends(get_user_repository)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    jwt_token = authorization.split(" ")[1]
    try:
        sub, exp = await user_repo._decode_jwt_token(jwt_token)
        id = sub
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    specialist = await org_repo.get_specialist_profile(id)
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")
    return specialist

@router.get('/{specialist_id}', response_model=Specialist)
async def get_specialist_by_id(
    specialist_id: int,
    specialist_repo: PostgresSpecialistRepo = Depends(get_specialist_repository)
):
    specialist = await specialist_repo.get_specialist_profile(specialist_id)
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")
    return specialist