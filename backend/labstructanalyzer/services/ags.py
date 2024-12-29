import requests
from pylti1p3.assignments_grades import AssignmentsGradesService
from pylti1p3.message_launch import MessageLaunch
from starlette import status
from starlette.responses import JSONResponse

from pylti1p3.lineitem import LineItem
from pylti1p3.service_connector import REQUESTS_USER_AGENT

from labstructanalyzer.core.exceptions import AgsNotSupportedException
from labstructanalyzer.models.template import Template


class AgsService:
    """
    Служебные методы для работы с линиями оценок LTI AGS.
    Методы по обновлению и удалению линии реализованы как часть отсутствующего функционала в библиотеке
    и должны быть заменены на методы библиотеки при их появлении.
    https://github.com/dmitry-viskov/pylti1.3/pull/125
    """

    def __init__(self, message_launch: MessageLaunch):
        self.message_launch = message_launch

    def create_lineitem(self, template: Template):
        """
        Создает lineitem по шаблону с тэгом, равным id шаблона и именем, равным имени шаблона

        Args:
            template: Шаблон, не являющийся черновиком. Создание линии для черновика не приведет к ошибке
        """
        if not self.message_launch.has_ags():
            raise AgsNotSupportedException

        ags = self.message_launch.get_ags()
        lineitem = self._create_lineitem_object(template)
        return ags.find_or_create_lineitem(lineitem)

    def update_lineitem(self, template: Template):
        """
        Обновляет существующий lineitem. Если lineitem не существует, то будет создан новый.
        """
        if not self.message_launch.has_ags():
            raise AgsNotSupportedException

        ags = self.message_launch.get_ags()
        existing_lineitem = ags.find_lineitem_by_tag(str(template.template_id))
        if not existing_lineitem:
            self.create_lineitem(template)

        updated_lineitem = self._create_lineitem_object(template)
        updated_lineitem.set_id(existing_lineitem.get_id())

        request_headers = self._create_ags_request_headers()
        requests.Session().put(updated_lineitem.get_id(), data=updated_lineitem.get_value(), headers=request_headers)

    def delete_lineitem(self, template_id):
        """
        Удаляет lineitem по тэгу (== template_id).

        Args:
            template_id: id шаблона
        """
        if not self.message_launch.has_ags():
            raise AgsNotSupportedException

        ags = self.message_launch.get_ags()
        lineitem = ags.find_lineitem_by_tag(str(template_id))

        if not lineitem:
            return

        request_headers = self._create_ags_request_headers()
        requests.Session().delete(lineitem.get_id(), headers=request_headers)

    def _create_lineitem_object(self, template: Template):
        """
        Создает объект линии оценки для последующего сохранения средствами AGS
        """
        return LineItem(
            {
                "label": template.name,
                "scoreMaximum": template.max_score,
                "tag": str(template.template_id)
            }
        )

    def _create_ags_request_headers(self):
        """
        Описывает все необходимые заголовки, включая токен доступа, для изменения данных AGS
        """
        service_data = self.message_launch.get_launch_data().get("https://purl.imsglobal.org/spec/lti-ags/claim/endpoint")
        access_token = self.message_launch.get_service_connector().get_access_token(service_data["scope"])

        return {
            "User-Agent": REQUESTS_USER_AGENT,
            "Content-Type": "application/vnd.ims.lis.v2.lineitem+json",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.ims.lis.v2.lineitem+json"
        }
