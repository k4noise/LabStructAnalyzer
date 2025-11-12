import unittest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException

from labstructanalyzer.services.lti.ags import AgsService, AgsNotSupportedException, LtiException
from labstructanalyzer.services.background_task import BackgroundTaskService
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

        self.mock_background_task_service = MagicMock(spec=BackgroundTaskService)

        with patch('labstructanalyzer.services.lti.ags.GlobalLogger'):
            self.service = AgsService(self.mock_message_launch, self.mock_background_task_service)

    def test_init_raises_exception_if_ags_not_supported(self):
        """Инициализация должна падать, если AGS не поддерживается"""
        self.mock_message_launch.has_ags.return_value = False
        with self.assertRaises(AgsNotSupportedException):
            AgsService(self.mock_message_launch, self.mock_background_task_service)

    def test_create_lineitem_draft_template(self):
        """`create_lineitem` должен возвращать None для черновика и не ставить задачу в очередь"""
        draft_template = MockTemplate(is_draft=True)
        result = self.service.create_lineitem(draft_template)
        self.assertIsNone(result)
        self.mock_background_task_service.enqueue.assert_not_called()

    def test_create_lineitem_enqueues_task(self):
        """`create_lineitem` должен ставить задачу в очередь для не-черновика"""
        result = self.service.create_lineitem(self.mock_template)
        self.mock_background_task_service.enqueue.assert_called_once_with(
            self.service.find_or_create_lineitem,
            self.mock_template
        )
        self.assertIsNotNone(result)

    def test_find_or_create_lineitem_calls_ags_method(self):
        """`find_or_create_lineitem` должен вызывать метод AGS с корректными параметрами"""
        expected_lineitem = LineItem({
            "label": "Test Assignment",
            "scoreMaximum": 100.0,
            "resourceId": "123",
            "submissionReview": {
                "label": "Открыть работу"
            }
        })
        self.mock_ags.find_or_create_lineitem.return_value = expected_lineitem

        result = self.service.find_or_create_lineitem(self.mock_template)

        self.mock_ags.find_or_create_lineitem.assert_called_once()
        called_lineitem = self.mock_ags.find_or_create_lineitem.call_args[0][0]
        self.assertEqual(called_lineitem.get_label(), "Test Assignment")
        self.assertEqual(called_lineitem.get_score_maximum(), 100.0)
        self.assertEqual(called_lineitem.get_resource_id(), "123")
        self.assertEqual(result, expected_lineitem)

    def test_update_lineitem_no_changes(self):
        """`update_lineitem` не должен ставить задачу в очередь, если нет изменений"""
        existing_lineitem = LineItem({
            "id": "http://example.com/lineitem/1",
            "label": "Test Assignment",
            "scoreMaximum": 100.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = existing_lineitem

        with patch.object(self.service, '_build_ags_request_headers', return_value={}):
            self.service.update_lineitem(self.mock_template)

        self.mock_background_task_service.enqueue.assert_not_called()

    def test_update_lineitem_with_changes(self):
        """`update_lineitem` должен ставить задачу в очередь при наличии изменений"""
        existing_lineitem = LineItem({
            "id": "http://example.com/lineitem/1",
            "label": "Old Name",
            "scoreMaximum": 50.0,
            "resourceId": "123"
        })
        self.mock_ags.find_or_create_lineitem.return_value = existing_lineitem

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            self.service.update_lineitem(self.mock_template)

        self.mock_background_task_service.enqueue.assert_called_once()
        call_args = self.mock_background_task_service.enqueue.call_args
        self.assertEqual(call_args.args[0], self.service._execute_request)
        self.assertEqual(call_args.kwargs['method'], 'PUT')
        self.assertEqual(call_args.kwargs['url'], "http://example.com/lineitem/1")
        self.assertIn('scoreMaximum', call_args.kwargs['data'])
        self.assertIn('label', call_args.kwargs['data'])

    def test_delete_lineitem_not_found(self):
        """`delete_lineitem` не должен ставить задачу в очередь, если lineitem не найден"""
        self.mock_ags.find_lineitem_by_resource_id.return_value = None

        self.service.delete_lineitem(123)

        self.mock_background_task_service.enqueue.assert_not_called()

    def test_delete_lineitem_success(self):
        """`delete_lineitem` должен ставить задачу в очередь при успешном поиске"""
        existing_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_lineitem_by_resource_id.return_value = existing_lineitem

        with patch.object(self.service, '_build_ags_request_headers', return_value={"Authorization": "Bearer token"}):
            self.service.delete_lineitem(123)

        self.mock_background_task_service.enqueue.assert_called_once()
        call_args = self.mock_background_task_service.enqueue.call_args
        self.assertEqual(call_args.args[0], self.service._execute_request)
        self.assertEqual(call_args.kwargs['method'], 'DELETE')
        self.assertEqual(call_args.kwargs['url'], "http://example.com/lineitem/1")
        self.assertNotIn('data', call_args.kwargs)

    def test_set_grade_enqueues_task(self):
        """`set_grade` должен ставить задачу в очередь с корректными параметрами"""
        mock_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_or_create_lineitem.return_value = mock_lineitem
        user_id = "student-007"
        grade_value = 85.5

        self.service.set_grade(self.mock_template, user_id, grade_value)

        self.mock_background_task_service.enqueue.assert_called_once()
        call_args = self.mock_background_task_service.enqueue.call_args
        self.assertEqual(call_args.args[0], self.service.ags.put_grade)
        self.assertIsInstance(call_args.args[1], Grade)
        self.assertEqual(call_args.args[1].get_score_given(), grade_value)
        self.assertEqual(call_args.args[1].get_score_maximum(), self.mock_template.max_score)
        self.assertEqual(call_args.args[1].get_user_id(), user_id)
        self.assertEqual(call_args.args[2], mock_lineitem)

    def test_build_lineitem_object(self):
        """`_build_lineitem_object` должен создавать правильный объект LineItem с submissionReview"""
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

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_execute_request_success(self, mock_session_class):
        """`_execute_request` должен успешно выполнять запрос"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value.__enter__.return_value = mock_session

        headers = {"Authorization": "Bearer token"}
        with patch.object(self.service, '_build_ags_request_headers', return_value=headers):
            self.service._execute_request('PUT', 'http://example.com/lineitem/1', {'test': 'data'})

        mock_session.request.assert_called_once_with(
            'PUT',
            'http://example.com/lineitem/1',
            headers=headers,
            json={'test': 'data'}
        )

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_execute_request_error(self, mock_session_class):
        """`_execute_request` должен бросать LtiException при ошибке запроса"""
        mock_session = Mock()
        mock_session.request.side_effect = RequestException("Connection error")
        mock_session_class.return_value.__enter__.return_value = mock_session

        headers = {"Authorization": "Bearer token"}
        with patch.object(self.service, '_build_ags_request_headers', return_value=headers):
            with self.assertRaises(LtiException) as context:
                self.service._execute_request('PUT', 'http://example.com/lineitem/1', {'test': 'data'})

        self.assertIn("Ошибка LMS: Connection error", str(context.exception))
