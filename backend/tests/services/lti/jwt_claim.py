import unittest
from unittest.mock import Mock, patch

from labstructanalyzer.services.lti.jwt import JwtClaimService
from labstructanalyzer.models.user_model import UserRole


class TestJwtClaim(unittest.TestCase):
    def setUp(self):
        self.jwt_service = JwtClaimService()

        self.expected_roles = [UserRole.STUDENT, UserRole.ASSISTANT]
        self.expected_launch_id = "launch-123"
        self.expected_course_id = "course-abc"
        self.expected_claims = {
            "roles": self.expected_roles,
            "launch_id": self.expected_launch_id,
            "course_id": self.expected_course_id
        }

    def test_create_user_claims_at_jwt_object(self):
        """Метод корректно создает claims из "сырого" словаря JWT"""
        raw_jwt_data = {
            "roles": self.expected_roles,
            "launch_id": self.expected_launch_id,
            "course_id": self.expected_course_id,
            "some_other_field": "ignore_me"
        }

        result_claims = self.jwt_service.create_user_claims_at_jwt_object(raw_jwt_data)

        self.assertEqual(result_claims, self.expected_claims)

    @patch('labstructanalyzer.services.lti.jwt.CourseService')
    @patch('labstructanalyzer.services.lti.jwt.UserService')
    def test_create_user_claims_at_message_launch(self, mock_user_service_class, mock_course_service_class):
        """Метод корректно создает claims, используя зависимости UserService и CourseService"""
        mock_user_service_instance = mock_user_service_class.return_value
        mock_user_service_instance.roles = self.expected_roles

        mock_course_service_instance = mock_course_service_class.return_value
        mock_course_service_instance.id = self.expected_course_id

        mock_message_launch = Mock()
        mock_message_launch.get_launch_id.return_value = self.expected_launch_id

        result_claims = self.jwt_service.create_user_claims_at_message_launch(mock_message_launch)

        self.assertEqual(result_claims, self.expected_claims)
        mock_user_service_class.assert_called_once_with(mock_message_launch)
        mock_course_service_class.assert_called_once_with(mock_message_launch)
