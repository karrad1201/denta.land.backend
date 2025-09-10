from src.domain.entity.users.user import User
from src.infrastructure.repository.schemas.user_orm import Role
from enum import Enum


class AdminRoles(Enum):
    HELPER = 'helper'
    MODERATOR = 'moderator'
    TECH_ADMIN = 'tech_admin'
    ADMINISTRATOR = 'administrator'


class Admin(User):
    role: Role = Role.ADMIN
    admin_role: AdminRoles
    is_superadmin: bool = False
