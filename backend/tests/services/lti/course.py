import unittest
from unittest.mock import Mock

from labstructanalyzer.services.lti.course import CourseService

LTI_CONTEXT_CLAIM = "https://purl.imsglobal.org/spec/lti/claim/context"


class TestCourseService(unittest.TestCase):
    def test_properties_success_when_data_is_present(self):
        """
        Свойства `id` и `name` корректно извлекаются,
        когда все данные присутствуют в LTI-запуске
        """
        mock_launch_data = {
            LTI_CONTEXT_CLAIM: {
                "id": "course-xyz-789",
                "title": "Advanced Quantum Physics"
            }
        }

        mock_message_launch = Mock()
        mock_message_launch.get_launch_data.return_value = mock_launch_data

        course_service = CourseService(mock_message_launch)

        self.assertEqual(course_service.id, "course-xyz-789")
        self.assertEqual(course_service.name, "Advanced Quantum Physics")

    def test_raises_attribute_error_when_context_is_missing(self):
        """
        Код должен упасть с AttributeError, если
        блок 'context' полностью отсутствует, так как это нештатная ситуация
        """
        mock_launch_data = {}
        mock_message_launch = Mock()
        mock_message_launch.get_launch_data.return_value = mock_launch_data

        course_service = CourseService(mock_message_launch)

        with self.assertRaises(AttributeError):
            _ = course_service.name
        with self.assertRaises(AttributeError):
            _ = course_service.id

    def test_properties_return_none_when_context_is_empty(self):
        """
        Свойства должны возвращать None, если
        блок 'context' пуст
        """
        mock_launch_data = {
            LTI_CONTEXT_CLAIM: {}
        }
        mock_message_launch = Mock()
        mock_message_launch.get_launch_data.return_value = mock_launch_data

        course_service = CourseService(mock_message_launch)

        self.assertIsNone(course_service.name)
        self.assertIsNone(course_service.id)

    def test_properties_return_none_for_partially_missing_keys(self):
        """
        Проверяем корректную работу, если часть
        ключей в 'context' отсутствует
        """
        mock_launch_data = {
            LTI_CONTEXT_CLAIM: {
                "title": "History of Art"
            }
        }
        mock_message_launch = Mock()
        mock_message_launch.get_launch_data.return_value = mock_launch_data

        course_service = CourseService(mock_message_launch)

        self.assertEqual(course_service.name, "History of Art")
        self.assertIsNone(course_service.id)
