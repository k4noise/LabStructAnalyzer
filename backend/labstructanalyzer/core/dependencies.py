from typing import Generator

from fastapi import Depends
from fastapi_another_jwt_auth import AuthJWT
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from labstructanalyzer.configs.config import TOOL_CONF, GENERATE_MODEL_DIR
from labstructanalyzer.core.database import get_session
from labstructanalyzer.exceptions.access_denied import RoleAccessDeniedException
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.repository.answer import AnswerRepository
from labstructanalyzer.repository.report import ReportRepository
from labstructanalyzer.repository.template import TemplateRepository
from labstructanalyzer.repository.template_element import TemplateElementRepository
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.background_task import BackgroundTaskService
from labstructanalyzer.services.grade import GradeService
from labstructanalyzer.utils.hint_generator import HintGenerator
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.course import CourseService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pylti1p3.cache import FastAPICacheDataStorage
from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.request import FastAPIRequest
from labstructanalyzer.services.report import ReportService
from labstructanalyzer.services.template import TemplateService
from labstructanalyzer.services.template_element import TemplateElementService
from labstructanalyzer.utils.files.hybrid_storage import HybridStorage
from labstructanalyzer.utils.files.s3 import S3Storage
from labstructanalyzer.utils.ttl_cache import RedisCache


def get_user(authorize: AuthJWT = Depends()) -> User:
    """Возвращает минимально необходимые данные пользователя из токена"""
    authorize.jwt_required()
    payload = authorize.get_raw_jwt()
    user = User(**payload)
    return user


def get_cache(request: Request) -> RedisCache:
    return request.app.state.cache


def get_file_storage():
    return HybridStorage(backup=S3Storage())


def get_background_task_service(cache: RedisCache = Depends(get_cache)) -> BackgroundTaskService:
    return BackgroundTaskService(cache.get_connection())


def get_cache_data_storage(cache: RedisCache = Depends(get_cache)) -> FastAPICacheDataStorage:
    return FastAPICacheDataStorage(cache)


def get_message_launch(
        request: Request,
        user: User = Depends(get_user),
        cache_storage: FastAPICacheDataStorage = Depends(get_cache_data_storage)
) -> FastAPIMessageLaunch:
    return FastAPIMessageLaunch.from_cache(
        user.launch_id,
        FastAPIRequest(request),
        TOOL_CONF,
        launch_data_storage=cache_storage
    )


def get_nrps_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch)
) -> Generator[NrpsService, None, None]:
    with NrpsService(message_launch) as nrps:
        yield nrps


def get_ags_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch),
        background_task_service: BackgroundTaskService = Depends(get_background_task_service)
) -> AgsService:
    return AgsService(message_launch, background_task_service)


def get_course_service(
        message_launch: FastAPIMessageLaunch = Depends(get_message_launch)
) -> CourseService:
    return CourseService(message_launch)


def get_template_service(session: AsyncSession = Depends(get_session)) -> TemplateService:
    return TemplateService(TemplateRepository(session), TemplateElementService(TemplateElementRepository(session)))


def get_report_service(session: AsyncSession = Depends(get_session)) -> ReportService:
    return ReportService(ReportRepository(session), AnswerService(AnswerRepository(session)))


def get_grade_service(report_service: ReportService = Depends(get_report_service),
                      background_task_service: BackgroundTaskService = Depends(get_background_task_service),
                      ags_service: AgsService = Depends(get_ags_service),
                      nrps_service: NrpsService = Depends(get_nrps_service)) -> GradeService:
    return GradeService(report_service, background_task_service, ags_service, nrps_service)


def get_hint_generator(request: Request):
    return HintGenerator(GENERATE_MODEL_DIR)


def get_user_with_any_role(*roles: UserRole):
    """Возвращает данные пользователя, если он имеет хотя бы одну необходимую роль"""

    async def require_any_of_roles(user: User = Depends(get_user)) -> User:
        if not any(role in roles for role in user.roles):
            raise RoleAccessDeniedException()
        return user

    return require_any_of_roles
