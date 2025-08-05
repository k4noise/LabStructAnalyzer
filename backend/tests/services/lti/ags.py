import unittest
from unittest.mock import Mock, patch, MagicMock

from labstructanalyzer.services.lti.ags import AgsService, AgsNotSupportedException, LtiException
from pylti1p3.lineitem import LineItem
from pylti1p3.grade import Grade

MockTemplate = Mock()


class TestAgsService(unittest.TestCase):
    def setUp(self):
        self.mock_message_launch = MagicMock()
        self.mock_message_launch.has_ags.return_value = True

        self.mock_ags = self.mock_message_launch.get_ags.return_value

        self.mock_template = MockTemplate()
        self.mock_template.template_id = 123
        self.mock_template.name = "Test Assignment"
        self.mock_template.max_score = 100.0

        self.service = AgsService(self.mock_message_launch)

    def test_init_raises_exception_if_ags_not_supported(self):
        """Инициализация должна падать, если AGS не поддерживается"""
        self.mock_message_launch.has_ags.return_value = False
        with self.assertRaises(AgsNotSupportedException):
            AgsService(self.mock_message_launch)

    def test_create_lineitem(self):
        """`create_lineitem` должен вызывать `find_or_create_lineitem` с корректным объектом LineItem"""
        self.service.create_lineitem(self.mock_template)

        self.mock_ags.find_or_create_lineitem.assert_called_once()

        called_with_lineitem = self.mock_ags.find_or_create_lineitem.call_args[0][0]
        self.assertIsInstance(called_with_lineitem, LineItem)
        self.assertEqual(called_with_lineitem.get_label(), "Test Assignment")
        self.assertEqual(called_with_lineitem.get_resource_id(), "123")

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_update_lineitem_success(self, mock_requests_session):
        """`update_lineitem` обновляет существующий lineitem через PUT-запрос"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_session.return_value.put.return_value = mock_response

        mock_existing_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_lineitem_by_resource_id.return_value = mock_existing_lineitem

        self.mock_message_launch.get_service_connector.return_value.get_access_token.return_value = "fake-token"

        self.service.update_lineitem(self.mock_template)

        self.mock_ags.find_lineitem_by_resource_id.assert_called_once_with("123")
        mock_requests_session.return_value.put.assert_called_once()
        call_args, call_kwargs = mock_requests_session.return_value.put.call_args
        self.assertEqual(call_args[0], "http://example.com/lineitem/1")
        self.assertIn("Authorization", call_kwargs['headers'])
        self.assertEqual(call_kwargs['headers']['Authorization'], "Bearer fake-token")

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_update_lineitem_creates_if_not_exists(self, mock_requests_session):
        """`update_lineitem` вызывает `create_lineitem`, если lineitem не найден"""
        self.mock_ags.find_lineitem_by_resource_id.return_value = None

        with patch.object(self.service, 'create_lineitem') as mock_create_method:
            try:
                self.service.update_lineitem(self.mock_template)
            except Exception:
                pass

            mock_create_method.assert_called_once_with(self.mock_template)

    @patch('labstructanalyzer.services.lti.ags.requests.Session')
    def test_delete_lineitem_success(self, mock_requests_session):
        """`delete_lineitem` вызывает DELETE-запрос, если lineitem найден"""
        mock_existing_lineitem = LineItem({"id": "http://example.com/lineitem/1"})
        self.mock_ags.find_lineitem_by_resource_id.return_value = mock_existing_lineitem
        self.mock_message_launch.get_service_connector.return_value.get_access_token.return_value = "fake-token"

        self.service.delete_lineitem(self.mock_template.template_id)

        mock_requests_session.return_value.delete.assert_called_once_with(
            "http://example.com/lineitem/1",
            headers=unittest.mock.ANY
        )

    def test_set_grade(self):
        """`set_grade` вызывает `put_grade` с корректно сформированным объектом Grade"""
        mock_lineitem = LineItem()
        self.mock_ags.find_lineitem_by_resource_id.return_value = mock_lineitem
        user_id = "student-007"
        grade_value = 85.5

        self.service.set_grade(self.mock_template, user_id, grade_value)

        self.mock_ags.put_grade.assert_called_once()

        called_with_grade = self.mock_ags.put_grade.call_args[0][0]
        self.assertIsInstance(called_with_grade, Grade)
        self.assertEqual(called_with_grade.get_score_given(), grade_value)
        self.assertEqual(called_with_grade.get_score_maximum(), self.mock_template.max_score)
        self.assertEqual(called_with_grade.get_user_id(), user_id)
        self.assertEqual(called_with_grade.get_grading_progress(), "FullyGraded")
