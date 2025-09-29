import unittest
from unittest.mock import Mock, patch, MagicMock

from labstructanalyzer.services.lti.ags import AgsService, AgsNotSupportedException, LtiException
from pylti1p3.lineitem import LineItem
from pylti1p3.grade import Grade


class MockTemplate:
    def __init__(self, template_id=123, name="Test Assignment", max_score=100.0, is_draft=False):
        self.id = template_id
        self.name = name
        self.max_score = max_score
        self.is_draft = is_draft


class TestAgsService(unittest.TestCase):
    def setUp(self):
        self.mock_message_launch = MagicMock()
        self.mock_message_launch.has_ags.return_value = True
        self.mock_ags = self.mock_message_launch.get_ags.return_value
        self.mock_template = MockTemplate()

        with patch('labstructanalyzer.services.lti.ags.GlobalLogger'):
            self.service = AgsService(self.mock_message_launch)

    def test_init_raises_exception_if_ags_not_supported(self):
        """Инициализация должна падать, если AGS не поддерживается"""
        self.mock_message_launch.has_ags.return_value = False
        with self.assertRaises(AgsNotSupportedException):
            AgsService(self.mock_message_launch)

    def test_find_or_create_lineitem_draft_template(self):
        """`find_or_create_lineitem` должен возвращать None для черновика"""
        draft_template = MockTemplate(is_draft=True)
        result = self.service.find_or_create_lineitem(draft_template)
        self.assertIsNone(result)

    def test_find_or_create_lineitem_calls_ags_method(self):
        """`find_or_create_lineitem` должен вызывать метод AGS с корректными параметрами"""
        expected_lineitem = LineItem({
            "label": "Test Assignment",
            "scoreMaximum": 100.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = expected_lineitem

        result = self.service.find_or_create_lineitem(self.mock_template)

        self.mock_ags.find_or_create_lineitem.assert_called_once()
        called_lineitem = self.mock_ags.find_or_create_lineitem.call_args[0][0]
        self.assertEqual(called_lineitem.get_label(), "Test Assignment")
        self.assertEqual(called_lineitem.get_score_maximum(), 100.0)
        self.assertEqual(called_lineitem.get_resource_id(), "123")
        self.assertEqual(result, expected_lineitem)

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_update_lineitem_no_changes(self, mock_requests_session):
        """`update_lineitem` не должен делать запрос, если нет изменений"""
        existing_lineitem = LineItem({
            "id": "http://example.com/lineitem/1",
            "label": "Test Assignment",
            "scoreMaximum": 100.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = existing_lineitem

        with patch.object(self.service, '_build_ags_request_headers', return_value={}):
            self.service.update_lineitem(self.mock_template)

        mock_requests_session.return_value.put.assert_not_called()

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_update_lineitem_with_changes(self, mock_requests_session):
        """`update_lineitem` должен делать PUT-запрос при наличии изменений"""
        existing_lineitem = LineItem({
            "id": "http://example.com/lineitem/1",
            "label": "Old Name",
            "scoreMaximum": 50.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = existing_lineitem

        mock_response = Mock()
        mock_response.status_code = 200
        mock_session_instance = Mock()
        mock_session_instance.put.return_value = mock_response
        mock_requests_session.return_value.__enter__.return_value = mock_session_instance

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            self.service.update_lineitem(self.mock_template)

        mock_session_instance.put.assert_called_once()

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_update_lineitem_error_response(self, mock_requests_session):
        """`update_lineitem` должен бросать исключение при ошибке ответа"""
        existing_lineitem = LineItem({
            "id": "http://example.com/lineitem/1",
            "label": "Old Name",
            "scoreMaximum": 50.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = existing_lineitem

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_session_instance = Mock()
        mock_session_instance.put.return_value = mock_response
        mock_requests_session.return_value.__enter__.return_value = mock_session_instance

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            with self.assertRaises(LtiException):
                self.service.update_lineitem(self.mock_template)

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_delete_lineitem_not_found(self, mock_requests_session):
        """`delete_lineitem` не должен делать запрос, если lineitem не найден"""
        self.mock_ags.find_lineitem_by_resource_id.return_value = None

        mock_session_instance = Mock()
        mock_requests_session.return_value.__enter__.return_value = mock_session_instance

        self.service.delete_lineitem(123)

        mock_session_instance.delete.assert_not_called()

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_delete_lineitem_success(self, mock_requests_session):
        """`delete_lineitem` должен делать DELETE-запрос при успешном поиске"""
        existing_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_lineitem_by_resource_id.return_value = existing_lineitem

        mock_response = Mock()
        mock_response.status_code = 204
        mock_session_instance = Mock()
        mock_session_instance.delete.return_value = mock_response
        mock_requests_session.return_value.__enter__.return_value = mock_session_instance

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            self.service.delete_lineitem(123)

        mock_session_instance.delete.assert_called_once_with(
            "http://example.com/lineitem/1",
            headers={"Authorization": "Bearer token"}
        )

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_delete_lineitem_error_response(self, mock_requests_session):
        """`delete_lineitem` должен бросать исключение при ошибке ответа"""
        existing_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_lineitem_by_resource_id.return_value = existing_lineitem

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_session_instance = Mock()
        mock_session_instance.delete.return_value = mock_response
        mock_requests_session.return_value.__enter__.return_value = mock_session_instance

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            with self.assertRaises(LtiException):
                self.service.delete_lineitem(123)

    def test_set_grade(self):
        """`set_grade` должен вызывать `put_grade` с корректно сформированным объектом Grade"""
        mock_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_or_create_lineitem.return_value = mock_lineitem
        user_id = "student-007"
        grade_value = 85.5

        self.service.set_grade(self.mock_template, user_id, grade_value)

        self.mock_ags.put_grade.assert_called_once()
        call_args = self.mock_ags.put_grade.call_args[0]
        called_grade = call_args[0]
        called_lineitem = call_args[1]

        self.assertIsInstance(called_grade, Grade)
        self.assertEqual(called_grade.get_score_given(), grade_value)
        self.assertEqual(called_grade.get_score_maximum(), self.mock_template.max_score)
        self.assertEqual(called_grade.get_user_id(), user_id)
        self.assertEqual(called_grade.get_grading_progress(), "FullyGraded")
        self.assertEqual(called_lineitem, mock_lineitem)

    def test_build_lineitem_object(self):
        """`_build_lineitem_object` должен создавать правильный объект LineItem"""
        lineitem = self.service._build_lineitem_object(self.mock_template)

        self.assertIsInstance(lineitem, LineItem)
        self.assertEqual(lineitem.get_label(), "Test Assignment")
        self.assertEqual(lineitem.get_score_maximum(), 100.0)
        self.assertEqual(lineitem.get_resource_id(), "123")

    def test_build_ags_request_headers(self):
        """`_build_ags_request_headers` должен создавать правильные заголовки"""
        mock_service_data = {"scope": ["https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"]}
        self.mock_message_launch.get_launch_data.return_value = {
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": mock_service_data
        }
        self.mock_message_launch.get_service_connector.return_value.get_access_token.return_value = "fake-token"

        headers = self.service._build_ags_request_headers()

        self.assertEqual(headers["User-Agent"], "PyLTI1p3-client")
        self.assertEqual(headers["Content-Type"], "application/vnd.ims.lis.v2.lineitem+json")
        self.assertEqual(headers["Authorization"], "Bearer fake-token")
        self.assertEqual(headers["Accept"], "application/vnd.ims.lis.v2.lineitem+json")
