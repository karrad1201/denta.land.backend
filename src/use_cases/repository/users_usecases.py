from src.domain.interfaces.user.user_repositiry import IUserRepository
from src.domain.interfaces.user.specialistic_repository import ISpecialistRepository
from src.domain.interfaces.user.patient_repository import IPatientRepository
from src.domain.interfaces.user.organization_repository import IOrganizationRepository
from src.domain.interfaces.user.admin_repository import IAdminRepository
from src.domain.entity.users.user import UserInput, User, Role as UserRole, UserFull
from src.domain.entity.users.specialist.specialist import Specialist
from src.domain.entity.users.patient.patient import Patient
from src.domain.entity.users.organization.organization import Organization
from src.domain.entity.users.admin.admin_entity import Admin, AdminRoles
from src.infrastructure.adapters.orm_entity_adapter import UserOrmEntityAdapter
from src.domain.interfaces.user.user_repositiry import SettingsUserData
from typing import Dict, Union
import logging
from pydantic import ValidationError


class RegistrationUseCase:
    def __init__(
            self,
            user_repo: IUserRepository,
            specialist_repo: ISpecialistRepository,
            patient_repo: IPatientRepository,
            org_repo: IOrganizationRepository,
            admin_repo: IAdminRepository,
            adapter: UserOrmEntityAdapter
    ):
        self._user_repo = user_repo
        self._specialist_repo = specialist_repo
        self._patient_repo = patient_repo
        self._org_repo = org_repo
        self._admin_repo = admin_repo
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    async def execute(
            self,
            input_data: Dict
    ) -> Union[User, Specialist, Patient, Organization, Admin]:
        try:
            self._logger.debug(f"Registration input_data: {input_data}")
            email = input_data.get('email', input_data.get('mail', ''))
            if not email:
                raise ValueError('Email is required for registration')

            base_fields = {
                'nickname': input_data['nickname'],
                'name': input_data['name'],
                'role': str(input_data.get('role', 'patient')),
                'password': input_data['password'],
                'photo_path': input_data.get('photo_path'),
                'country': input_data.get('country', ''),
                'email': email,
                'phone_number': input_data.get('phone_number')
            }

            user_input = UserInput(
                id=None,
                **base_fields,
                password_hash="",
            )

            if await self._user_repo.check_nickname_exists(user_input.nickname):
                raise ValueError("Nickname already exists")

            if await self._user_repo.check_email_exists(user_input.email):
                raise ValueError("Email already exists")

            hashed_password = await self._hash_password(user_input.password)
            user_input.password_hash = hashed_password

            base_user = await self._user_repo.create(user_input)

            role_str = str(input_data.get('role', 'patient')).lower()
            if role_str == 'specialist':
                return await self._create_specialist_profile(base_user.id, input_data)
            elif role_str == 'patient':
                return await self._create_patient_profile(base_user.id, input_data)
            elif role_str == 'organization':
                return await self._create_organization_profile(base_user.id, input_data)
            elif role_str == 'admin':
                return await self._create_admin_profile(base_user.id, input_data)
            return base_user

        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Registration error: {e}")
            await self._user_repo.session.rollback()
            raise

    async def _create_specialist_profile(self, user_id: int, data: Dict) -> Specialist:
        return await self._specialist_repo.create_specialist_profile(
            user_id=user_id,
            specifications=data['specifications'],
            qualification=data['qualification'],
            experience=data.get('experience_years', 0)
        )

    async def _create_patient_profile(self, user_id: int, data: Dict) -> Patient:
        return await self._patient_repo.create_patient_profile(
            user_id=user_id,
            city=data['city']
        )

    async def _create_organization_profile(self, user_id: int, data: Dict) -> Organization:
        return await self._org_repo.create_organization_profile(
            user_id=user_id,
            locations=data['locations']
        )

    async def _create_admin_profile(self, user_id: int, data: Dict) -> Admin:
        """Создание профиля администратора"""
        return await self._admin_repo.create_admin_profile(
            user_id=user_id,
            admin_role=data['admin_role'],
            is_superadmin=data.get('is_superadmin', False)
        )

    async def _hash_password(self, password: str) -> str:
        from src.infrastructure.services.registration.hash_password import hash_password
        return await hash_password(password)


class LoginUseCase:
    def __init__(
            self,
            user_repo: IUserRepository,
            patient_repo: IPatientRepository,
            specialist_repo: ISpecialistRepository,
            org_repo: IOrganizationRepository,
            admin_repo: IAdminRepository,
            adapter: UserOrmEntityAdapter
    ):
        self._user_repo = user_repo
        self._patient_repo = patient_repo
        self._specialist_repo = specialist_repo
        self._org_repo = org_repo
        self._admin_repo = admin_repo
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    async def execute(self, nickname: str, password: str) -> dict:
        user_orm = await self._user_repo.get_by_nickname(nickname)
        if not user_orm:
            raise ValueError("User not found")

        is_valid = await self._user_repo._verify_password(
            password,
            user_orm.password_hash
        )
        if not is_valid:
            raise ValueError("Invalid password")

        access_token = await self._user_repo._generate_jwt_token(user_orm.id)

        base_fields = {
            'id': user_orm.id,
            'nickname': user_orm.nickname,
            'name': user_orm.name,
            'role': user_orm.role,
            'photo_path': user_orm.photo_path,
            'country': user_orm.country,
            'email': user_orm.email,
            'phone_number': user_orm.phone_number,
            'created_at': user_orm.created_at,
        }

        if user_orm.role == "patient":
            profile = await self._patient_repo.get_patient_profile(user_orm.id)
            result = Patient(**{**base_fields, **profile.dict()})
        elif user_orm.role == "specialist":
            profile = await self._specialist_repo.get_specialist_profile(user_orm.id)
            result = Specialist(**{**base_fields, **profile.dict()})
        elif user_orm.role == "admin":
            profile = await self._admin_repo.get_admin_profile(user_orm.id)
            result = Admin(**{**base_fields, **profile.dict()})
        elif user_orm.role == "organization":
            profile = await self._org_repo.get_organization_profile(user_orm.id)
            result = Organization(**{**base_fields, **profile.dict()})
        else:
            result = User(**base_fields)

        return {
            "user": result,
            "access_token": access_token
        }

    async def _hash_password(self, password: str) -> str:
        from src.infrastructure.services.registration.hash_password import hash_password
        return await hash_password(password)


class SetSettingsUseCase:
    def __init__(
            self,
            user_repo: IUserRepository,
            patient_repo: IPatientRepository,
            specialist_repo: ISpecialistRepository,
            org_repo: IOrganizationRepository,
            admin_repo: IAdminRepository,
            adapter: UserOrmEntityAdapter
    ):
        self._user_repo = user_repo
        self._patient_repo = patient_repo
        self._specialist_repo = specialist_repo
        self._org_repo = org_repo
        self._admin_repo = admin_repo
        self._adapter = adapter
        self._logger = logging.getLogger(__name__)

    async def execute(self, update_data: Dict, jwt_token: str) -> str:
        import datetime
        try:
            user_id, expiration_time = await self._user_repo._decode_jwt_token(jwt_token)
            time = datetime.datetime.utcfromtimestamp(expiration_time)
            if time < datetime.datetime.utcnow():
                raise ValueError("JWT token expired")

            current_user = await self._user_repo.get_by_id(user_id)
            if not current_user:
                raise ValueError("User not found")

            admin_fields = {'admin_role', 'is_superadmin'}
            if any(field in update_data for field in admin_fields):
                if current_user.role != 'admin':
                    raise ValueError("Only admins can update admin fields")

                admin_profile = await self._admin_repo.get_admin_profile(user_id)
                if not admin_profile:
                    raise ValueError("Admin profile not found")

                self._check_admin_fields(update_data, admin_profile.admin_role)

            await self._update_base_fields(user_id, update_data, current_user)

            await self._update_role_profile(user_id, update_data, current_user.role)

            return "Settings updated successfully"
        except ValidationError as e:
            self._logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Settings update error: {e}")
            await self._user_repo.session.rollback()
            raise

    async def _update_base_fields(
            self,
            user_id: int,
            update_data: Dict,
            current_user: User
    ):
        base_fields = {}

        if 'nickname' in update_data and update_data['nickname'] != current_user.nickname:
            if await self._user_repo.check_nickname_exists(update_data['nickname']):
                raise ValueError("Nickname already exists")
            base_fields['nickname'] = update_data['nickname']

        if 'email' in update_data and update_data['email'] != current_user.email:
            if await self._user_repo.check_email_exists(update_data['email']):
                raise ValueError("Email already exists")
            base_fields['email'] = update_data['email']

        if 'password' in update_data:
            hashed_password = await self._hash_password(update_data['password'])
            base_fields['password_hash'] = hashed_password

        for field in ['name', 'photo_path', 'country', 'phone_number']:
            if field in update_data:
                base_fields[field] = update_data[field]

        if base_fields:
            await self._user_repo.update(user_id, base_fields)

    async def _update_role_profile(
            self,
            user_id: int,
            update_data: Dict,
            role: str
    ):
        role = role.lower()

        if role == "patient" and 'city' in update_data:
            await self._patient_repo.update_city(user_id, update_data['city'])

        elif role == "specialist":
            if 'specifications' in update_data:
                await self._specialist_repo.update_specialization(
                    user_id,
                    update_data['specifications']
                )
            if 'qualification' in update_data:
                await self._specialist_repo.add_qualification(
                    user_id,
                    update_data['qualification']
                )

        elif role == "organization" and 'locations' in update_data:
            await self._org_repo.update_locations(
                user_id,
                update_data['locations']
            )

        elif role == "admin":
            new_role = update_data.get('admin_role')
            is_superadmin = update_data.get('is_superadmin')
            if new_role or is_superadmin is not None:
                current_profile = await self._admin_repo.get_admin_profile(user_id)
                if not current_profile:
                    raise ValueError(f"Admin profile not found")

                await self._admin_repo.update_admin_privileges(
                    user_id,
                    new_role or current_profile.admin_role,
                    is_superadmin if is_superadmin is not None else current_profile.is_superadmin
                )

    async def _hash_password(self, password: str) -> str:
        from src.infrastructure.services.registration.hash_password import hash_password
        return await hash_password(password)

    def _check_admin_fields(self, update_data: Dict, role: AdminRoles):
        admin_fields = {'admin_role', 'is_superadmin'}
        role = role.value
        if any(field in update_data for field in admin_fields) and role.lower() != "administrator":
            raise ValueError(f"Only administrators can update admin fields, {update_data}, {role}")


from src.infrastructure.repository.user.postgres_admin_repo import PostgresAdminRepo


class AdminUseCase:
    def __init__(self, admin_repo: PostgresAdminRepo):
        self._admin_repo = admin_repo

    async def get_admin_profile(self, user_id: int) -> Admin:
        return await self._admin_repo.get_admin_profile(user_id)

    async def get_all_users(self, page: int, page_size: int) -> list[User]:
        return await self._admin_repo.get_all_users(page=page, page_size=page_size)

    async def block_user(self, user_id: int, reason: str):
        return await self._admin_repo.block_user(user_id=user_id, reason=reason)

    async def unblock_user(self, user_id: int):
        return await self._admin_repo.unblock_user(user_id=user_id)

    async def delete_user(self, user_id: int):
        return await self._admin_repo.delete_user(user_id=user_id)

    async def get_statisctics(self):
        return await self._admin_repo.get_statisctics()
