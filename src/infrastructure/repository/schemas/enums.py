# enums.py
from sqlalchemy import Enum as SQLAlchemyEnum

RoleEnum = SQLAlchemyEnum(
    'organization', 'specialist', 'patient', 'admin',
    name='user_role'
)

AdminRolesEnum = SQLAlchemyEnum(
    'helper', 'moderator', 'tech_admin', 'administrator',
    name='admin_role'
)

ResponseStatusEnum = SQLAlchemyEnum(
    'proposed', 'denied', 'taken', 'completed', 'prematurely_closed',
    name='response_status'
)

OrderStatusEnum = SQLAlchemyEnum(
    'active', 'inactive', 'completed', 'cancelled',
    name='order_status'
)

MessageTypeEnum = SQLAlchemyEnum(
    'text', 'voice', 'file', 'image',
    name='message_type'
)