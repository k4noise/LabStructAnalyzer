from typing import Generator

from fastapi import Depends
from fastapi_another_jwt_auth import AuthJWT
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from labstructanalyzer.configs.config import TOOL_CONF
from labstructanalyzer.core.database import get_session
from labstructanalyzer.exceptions.access_denied import RoleAccessDeniedException
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.repository.answer import AnswerRepository
from labstructanalyzer.repository.template import TemplateRepository
from labstructanalyzer.repository.template_element import TemplateElementRepository
from labstructanalyzer.routers.lti_router import cache
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.background_task import BackgroundTaskService
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.services.template_element import TemplateElementService
from labstructanalyzer.utils.files.chain_storage import ChainStorage


def get_template_service(session: AsyncSession = Depends(get_session)) -> TemplateService:
    return TemplateService(TemplateRepository(session), TemplateElementService(TemplateElementRepository(session)))


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(session)


def get_answer_service(session: AsyncSession = Depends(get_session)) -> AnswerService:
    return AnswerService(AnswerRepository(session))


def get_background_task_service(session: AsyncSession = Depends(get_session)) -> BackgroundTaskService:
    return BackgroundTaskService(session)


def get_user(authorize: AuthJWT = Depends()) -> User:
    """Возвращает минимально необходимые данные пользователя из токена"""
    authorize.jwt_required()
    payload = authorize.get_raw_jwt()
    user = User(**payload)
    return user


def get_chain_storage():
    return ChainStorage.get_default()


def get_message_launch(
        request: Request = Depends(),
        user: User = Depends(get_user)
) -> FastAPIMessageLaunch:
    launch_data_storage = FastAPICacheDataStorage(cache)
    return FastAPIMessageLaunch.from_cache(
        user.launch_id,
        FastAPIRequest(request),
        TOOL_CONF,
        launch_data_storage=launch_data_storage
    )


def get_nrps_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch)
) -> Generator[NrpsService, None, None]:
    with NrpsService(message_launch) as nrps:
        yield nrps


def get_ags_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch)
) -> AgsService:
    return AgsService(message_launch)


def get_course_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch)
) -> CourseService:
    return CourseService(message_launch)


def get_user_with_any_role(*roles: UserRole):
    """Возвращает данные пользователя, если он имеет хотя бы одну необходимую роль"""

    async def require_any_of_roles(user: User = Depends(get_user)) -> User:
        if not any(role in roles for role in user.roles):
            raise RoleAccessDeniedException()
        return user

    return require_any_of_roles
