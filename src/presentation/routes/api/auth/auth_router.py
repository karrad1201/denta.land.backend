from fastapi import APIRouter, status, Depends, HTTPException, Request
from src.domain.entity.users.user import User
from src.domain.entity.users.specialist.specialist import Specialist
from src.domain.entity.users.patient.patient import Patient
from src.domain.entity.users.organization.organization import Organization
from src.domain.entity.users.admin.admin_entity import Admin
from src.dependencies import get_registration_use_case, get_login_use_case, get_current_user_optional, get_admin_repository
from src.use_cases.repository.users_usecases import RegistrationUseCase, LoginUseCase
from src.infrastructure.repository.user.postgres_admin_repo import PostgresAdminRepo
from pydantic import BaseModel
from typing import Union, List, Optional
from src.domain.entity.users.user import Role
from src.domain.entity.users.admin.admin_entity import AdminRoles

router = APIRouter(prefix='/api/auth')


class LoginData(BaseModel):
    nickname: str
    password: str


class LoginResponse(BaseModel):
    user: Union[Patient, Specialist, Organization, Admin]
    access_token: str


class BaseRegisterData(BaseModel):
    nickname: str
    name: str
    password: str
    photo_path: Optional[str] = None
    country: str = ""
    email: str
    phone_number: str


class PatientRegisterData(BaseRegisterData):
    city: str


class SpecialistRegisterData(BaseRegisterData):
    specifications: List[str]
    qualification: str
    experience_years: int = 0


class OrganizationRegisterData(BaseRegisterData):
    locations: List[str]


class AdminRegisterData(BaseRegisterData):
    admin_role: AdminRoles
    is_superadmin: bool = False


# Объединенный тип для ответа
UserResponse = Union[User, Specialist, Patient, Organization, Admin]


async def require_administrator(
        current_user: User = Depends(get_current_user_optional)
):
    if not current_user or current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )

    admin_repo = await get_admin_repository()
    admin_profile = await admin_repo.get_admin_profile(current_user.id)
    if admin_profile.admin_role != AdminRoles.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user


@router.post(
    '/reg',
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "User created successfully"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"}
    }
)
async def register(
        request: Request,
        user_data: Union[
            PatientRegisterData,
            SpecialistRegisterData,
            OrganizationRegisterData,
            AdminRegisterData
        ],
        use_case: RegistrationUseCase = Depends(get_registration_use_case),
        login_use_case: LoginUseCase = Depends(get_login_use_case),
        current_user: User = Depends(get_current_user_optional),
        admin_repo: PostgresAdminRepo = Depends(get_admin_repository)
):
    try:
        data = user_data.model_dump()

        # Определяем роль
        if isinstance(user_data, PatientRegisterData):
            data['role'] = Role.PATIENT.value
        elif isinstance(user_data, SpecialistRegisterData):
            data['role'] = Role.SPECIALIST.value
        elif isinstance(user_data, OrganizationRegisterData):
            data['role'] = Role.ORGANIZATION.value
        elif isinstance(user_data, AdminRegisterData):
            data['role'] = Role.ADMIN.value


        if data.get('role') == Role.ADMIN.value:
            if not current_user or current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Доступ запрещен"
                )

            admin_profile = await admin_repo.get_admin_profile(current_user.id)

            if admin_profile.admin_role != AdminRoles.ADMINISTRATOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав"
                )

        registration_result = await use_case.execute(data)

        reg_data = vars(registration_result) if not isinstance(registration_result, dict) else registration_result

        password = data.get('password')
        nickname = data.get('nickname')

        login_result = await login_use_case.execute(nickname, password)
        login_data = vars(login_result) if not isinstance(login_result, dict) else login_result

        if 'user' in reg_data:
            return_data = {**reg_data['user'], 'access_token': login_data.get('access_token')}
        else:
            return_data = {
                **{k: v for k, v in reg_data.items() if k != 'access_token'},
                'access_token': login_data.get('access_token')
            }

        return return_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post('/login', response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
        user_data: LoginData,
        use_case: LoginUseCase = Depends(get_login_use_case)
):
    try:
        return await use_case.execute(user_data.nickname, user_data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
