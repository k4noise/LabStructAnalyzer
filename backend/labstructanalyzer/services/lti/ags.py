from datetime import datetime
from typing import Optional

import requests
from pylti1p3.exception import LtiException
from pylti1p3.grade import Grade
from pylti1p3.message_launch import MessageLaunch

from pylti1p3.lineitem import LineItem
from pylti1p3.service_connector import REQUESTS_USER_AGENT

from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.exceptions.lis_service_no_access import AgsNotSupportedException
from labstructanalyzer.schemas.template import TemplateStructure


class AgsService:
    """
    Служебные методы для работы с линиями оценок LTI AGS.
    Методы по обновлению и удалению линии реализованы как часть отсутствующего функционала в библиотеке
    и должны быть заменены на методы библиотеки при их появлении.
    https://github.com/dmitry-viskov/pylti1.3/pull/125
    """

    def __init__(self, message_launch: MessageLaunch):
        if not message_launch.has_ags():
            raise AgsNotSupportedException()

        self.message_launch = message_launch
        self.ags = self.message_launch.get_ags()
        self.logger = GlobalLogger().get_logger(__name__)

    def find_or_create_lineitem(self, template: TemplateStructure) -> Optional[LineItem]:
        """
        Создает lineitem по шаблону с тэгом, равным id шаблона и именем, равным имени шаблона.
        Если lineitem для этого шаблона уже существует, то ничего не делает.
        Для черновика создание линии игнорируется

        Args:
            template: Шаблон, не являющийся черновиком
        """
        if template.is_draft:
            self.logger.debug(f"Линия для черновика {template.id} не будет создаваться")
            return None
        lineitem = self._build_lineitem_object(template)
        return self.ags.find_or_create_lineitem(lineitem, "resource_id")

    def update_lineitem(self, template: TemplateStructure):
        """
        Обновляет существующий lineitem.
        Использовать метод следует **С БОЛЬШОЙ ОСТОРОЖНОСТЬЮ**,
        так как в некоторых LMS (например, Moodle) может приводить к временным ошибкам вида `gradesneedregrading`
        """
        lineitem = self.find_or_create_lineitem(template)
        original_values = lineitem.get_value()
        if lineitem.get_score_maximum() != template.max_score:
            lineitem.set_score_maximum(template.max_score)

        if lineitem.get_label() != template.name:
            lineitem.set_label(template.name)

        if original_values == lineitem.get_value():
            self.logger.debug(f"Линия не будет обновлена, изменения отсутствуют")
            return

        request_headers = self._build_ags_request_headers()

        with requests.Session() as session:
            response = session.put(
                lineitem.get_id(),
                data=lineitem.get_value(),
                headers=request_headers
            )
            if response.status_code not in (200, 204):
                raise LtiException(f"Ошибка LMS при обновлении линии оценок: {response.text}")
            self.logger.info(f"Обновлена линия оценок с id {template.id}")

    def delete_lineitem(self, template_id):
        """Удаляет lineitem по id шаблона"""
        lineitem = self.ags.find_lineitem_by_resource_id(str(template_id))

        if not lineitem:
            self.logger.warning(f"Попытка удаления несуществующей линии оценок {template_id}")
            return

        request_headers = self._build_ags_request_headers()
        with requests.Session() as session:
            response = session.delete(lineitem.get_id(), headers=request_headers)

            if response.status_code not in (200, 204):
                raise LtiException(f"Ошибка LMS: {response.text}")

            self.logger.info(f"Удалена линия оценок с id {template_id}")

    def set_grade(self, template: TemplateStructure, user_id: str, teacher_grade: float):
        """Передает оценку в LMS"""
        lineitem = self.find_or_create_lineitem(template)
        grade = Grade() \
            .set_score_given(teacher_grade) \
            .set_score_maximum(template.max_score) \
            .set_user_id(user_id) \
            .set_timestamp(datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000')) \
            .set_activity_progress('Completed') \
            .set_grading_progress('FullyGraded')

        self.ags.put_grade(grade, lineitem)
        self.logger.info(
            f"Передана оценка {teacher_grade}/{lineitem.get_score_maximum()} для шаблона {template.id} в LMS")

    def _build_lineitem_object(self, template: TemplateStructure):
        """
        Создает объект линии оценки для последующего сохранения средствами AGS
        """
        return LineItem(
            {
                "label": template.name,
                "scoreMaximum": template.max_score,
                "resourceId": str(template.id)
            }
        )

    def _build_ags_request_headers(self):
        """
        Описывает все необходимые заголовки, включая токен доступа, для изменения данных AGS
        """
        service_data = self.message_launch.get_launch_data().get(
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint")
        access_token = self.message_launch.get_service_connector().get_access_token(service_data["scope"])

        return {
            "User-Agent": REQUESTS_USER_AGENT,
            "Content-Type": "application/vnd.ims.lis.v2.lineitem+json",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.ims.lis.v2.lineitem+json"
        }
