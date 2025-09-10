from fastapi import APIRouter, status, Depends, HTTPException, Query
from src.dependencies import get_current_user, get_clinic_use_case
from src.domain.entity.users.user import User
from src.domain.entity.clinics.clinic_entity import Clinic
from src.use_cases.repository.clinics_usecases import ClinicUseCase
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix='/api/clinics', tags=['Clinics'])


class ClinicCreateRequest(BaseModel):
    organization_id: int
    name: str
    location: str
    address: str
    work_hours: Optional[dict] = None
    is_24_7: bool = False


class ClinicUpdateRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    work_hours: Optional[dict] = None
    is_24_7: Optional[bool] = None
    is_active: Optional[bool] = None


class ClinicResponse(Clinic):
    pass


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
        clinic_id: int,
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    clinic = await use_case.get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    if isinstance(clinic, Exception):
        raise HTTPException(status_code=500, detail=str(clinic))
    return clinic


@router.get("/by-location/", response_model=List[ClinicResponse])
async def get_clinics_by_location(
        location: str = Query(..., min_length=2),
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    clinics = await use_case.get_clinics_by_location(location, page, page_size)
    if isinstance(clinics, Exception):
        raise HTTPException(status_code=500, detail=str(clinics))
    return clinics


@router.get("/by-organization/{organization_id}", response_model=List[ClinicResponse])
async def get_clinics_by_organization(
        organization_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    clinics = await use_case.get_clinics_by_organization(organization_id, page, page_size)
    if isinstance(clinics, Exception):
        raise HTTPException(status_code=500, detail=str(clinics))
    return clinics


@router.post("/", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
        request: ClinicCreateRequest,
        current_user: User = Depends(get_current_user),
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    if current_user.role not in ["organization", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organizations and admins can create clinics"
        )

    if current_user.role == "organization" and current_user.id != request.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Organization can only create clinics for itself"
        )

    clinic_data = request.dict()
    clinic = await use_case.create_clinic(clinic_data)
    if isinstance(clinic, Exception):
        raise HTTPException(status_code=500, detail=str(clinic))
    return clinic


@router.put("/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(
        clinic_id: int,
        request: ClinicUpdateRequest,
        current_user: User = Depends(get_current_user),
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    clinic = await use_case.get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    if current_user.role == "organization" and current_user.id != clinic.organization_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own clinics"
        )

    if current_user.role not in ["organization", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organizations and admins can update clinics"
        )

    update_data = request.dict(exclude_unset=True)
    updated_clinic = await use_case.update_clinic(clinic_id, update_data)
    if isinstance(updated_clinic, Exception):
        raise HTTPException(status_code=500, detail=str(updated_clinic))
    return updated_clinic


@router.delete("/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinic(
        clinic_id: int,
        current_user: User = Depends(get_current_user),
        use_case: ClinicUseCase = Depends(get_clinic_use_case)
):
    clinic = await use_case.get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    if current_user.role == "organization" and current_user.id != clinic.organization_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own clinics"
        )

    if current_user.role not in ["organization", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only organizations and admins can delete clinics"
        )

    result = await use_case.delete_clinic(clinic_id)
    if isinstance(result, Exception):
        raise HTTPException(status_code=500, detail=str(result))
    return