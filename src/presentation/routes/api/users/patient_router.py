from fastapi import APIRouter, status, Depends, HTTPException
from src.dependencies import get_current_user, get_patient_repository
from src.domain.entity.users.user import User
from src.domain.entity.users.patient.patient import Patient
from src.infrastructure.repository.user.postgres_patient_repo import PostgresPatientRepo
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix='/api/patients', tags=['Patients'])

class PatientUpdateRequest(BaseModel):
    city: Optional[str] = None

@router.get('/me', response_model=Patient)
async def get_my_patient_profile(
    current_user: User = Depends(get_current_user),
    patient_repo: PostgresPatientRepo = Depends(get_patient_repository)
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can access this endpoint")

    patient = await patient_repo.get_patient_profile(current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

@router.get('/{patient_id}', response_model=Patient)
async def get_patient_by_id(
    patient_id: int,
    patient_repo: PostgresPatientRepo = Depends(get_patient_repository)
):
    patient = await patient_repo.get_patient_profile(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put('/me', response_model=Patient)
async def update_patient_profile(
    request: PatientUpdateRequest,
    current_user: User = Depends(get_current_user),
    patient_repo: PostgresPatientRepo = Depends(get_patient_repository)
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can update their profile")

    update_data = request.dict(exclude_unset=True)
    updated_patient = await patient_repo.update_patient_profile(current_user.id, update_data)
    if isinstance(updated_patient, Exception):
        raise HTTPException(status_code=500, detail=str(updated_patient))
    return updated_patient