from datetime import datetime

import requests
from pylti1p3.exception import LtiException
from pylti1p3.grade import Grade
from pylti1p3.message_launch import MessageLaunch

from pylti1p3.lineitem import LineItem
from pylti1p3.service_connector import REQUESTS_USER_AGENT

from labstructanalyzer.exceptions.lis_service_no_access import AgsNotSupportedException
from labstructanalyzer.models.template import Template


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

    def create_lineitem(self, template: Template):
        """
        Создает lineitem по шаблону с тэгом, равным id шаблона и именем, равным имени шаблона.
        Если lineitem для этого шаблона уже существует, то ничего не делает.

        Args:
            template: Шаблон, не являющийся черновиком. Создание линии для черновика не приведет к ошибке
        """
        ags = self.message_launch.get_ags()
        lineitem = self._create_lineitem_object(template)
        ags.find_or_create_lineitem(lineitem, "resource_id")

    def update_lineitem(self, template: Template):
        """
        Обновляет существующий lineitem.
        Использовать метод следует С БОЛЬШОЙ ОСТОРОЖНОСТЬЮ,
        так как в некоторых LMS (например, Moodle) может приводить к временным ошибкам вида `gradesneedregrading`
        """
        ags = self.message_launch.get_ags()
        existing_lineitem = ags.find_lineitem_by_resource_id(str(template.template_id))
        if not existing_lineitem:
            self.create_lineitem(template)
            return

        lineitem_with_new_data = self._create_lineitem_object(template)
        request_headers = self._create_ags_request_headers()

        response = requests.Session().put(
            existing_lineitem.get_id(),
            data=lineitem_with_new_data.get_value(),
            headers=request_headers
        )
        if response.status_code != 200:
            raise LtiException("Ошибка LMS")

    def delete_lineitem(self, template_id):
        """
        Удаляет lineitem по resourceId (== template_id).

        Args:
            template_id: id шаблона
        """
        ags = self.message_launch.get_ags()
        lineitem = ags.find_lineitem_by_resource_id(str(template_id))

        if not lineitem:
            return

        request_headers = self._create_ags_request_headers()
        requests.Session().delete(lineitem.get_id(), headers=request_headers)

    def set_grade(self, template: Template, user_id: str, grade: float):
        """
        Передает оценку в LMS
        """
        ags = self.message_launch.get_ags()
        lineitem = ags.find_lineitem_by_resource_id(str(template.template_id))
        grade = Grade() \
            .set_score_given(grade) \
            .set_score_maximum(template.max_score) \
            .set_user_id(user_id) \
            .set_timestamp(datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000')) \
            .set_activity_progress('Completed') \
            .set_grading_progress('FullyGraded')

        ags.put_grade(grade, lineitem)

    def _create_lineitem_object(self, template: Template):
        """
        Создает объект линии оценки для последующего сохранения средствами AGS
        """
        return LineItem(
            {
                "label": template.name,
                "scoreMaximum": template.max_score,
                "resourceId": str(template.template_id)
            }
        )

    def _create_ags_request_headers(self):
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
