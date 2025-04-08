from fastapi import Depends
from fastapi_another_jwt_auth import AuthJWT
from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.core.database import get_session
from labstructanalyzer.exceptions.access_denied import RoleAccessDeniedException
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.services.template import TemplateService


def get_template_service(session: AsyncSession = Depends(get_session)) -> TemplateService:
    return TemplateService(session)


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(session)


def get_answer_service(session: AsyncSession = Depends(get_session)) -> AnswerService:
    return AnswerService(session)


def get_user(authorize: AuthJWT = Depends()) -> User:
    """Возвращает минимально необходимые данные пользователя из токена"""
    authorize.jwt_required()
    payload = authorize.get_raw_jwt()
    user = User(**payload)
    return user


def get_user_with_any_role(*roles: UserRole):
    """Возвращает данные пользователя, если он имеет хотя бы одну необходимую роль"""

    async def require_any_of_roles(user: User = Depends(get_user)) -> User:
        if not any(role in roles for role in user.roles):
            raise RoleAccessDeniedException()
        return user

    return require_any_of_roles
