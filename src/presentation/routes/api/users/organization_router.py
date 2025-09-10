from fastapi import APIRouter, status, Depends, HTTPException, Header
from src.dependencies import get_organization_repository
from src.domain.entity.users.organization.organization import Organization
from src.infrastructure.repository.user.postgres_organization_repo import PostgresOrganizationRepo
from src.infrastructure.repository.user.postgres_user_repo import PostgresUserRepo
from src.dependencies import get_user_repository

router = APIRouter(prefix='/api/organizations', tags=['Organizations'])

@router.get('/me', response_model=Organization)
async def get_my_organization(
    org_repo: PostgresOrganizationRepo = Depends(get_organization_repository),
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
        organization_id = sub
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    organization = await org_repo.get_organization_profile(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@router.get('/{organization_id}', response_model=Organization)
async def get_organization_by_id(
    organization_id: int,
    org_repo: PostgresOrganizationRepo = Depends(get_organization_repository)
):
    organization = await org_repo.get_organization_profile(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

