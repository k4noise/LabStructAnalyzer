import unittest
from unittest.mock import Mock

from labstructanalyzer.schemas.user import NrpsUser
from labstructanalyzer.services.lti.user import UserService
from labstructanalyzer.models.user_model import UserRole


class TestUserService(unittest.TestCase):
    def setUp(self):
        self.mock_launch = Mock()
        self.mock_launch.get_launch_data.return_value = {"sub": "user-test-id"}

        self.mock_nrps = Mock()

    def test_id_property(self):
        """Свойство `id` корректно возвращает `sub` из данных запуска"""
        user_service = UserService(self.mock_launch)
        self.assertEqual(user_service.id, "user-test-id")

    def test_roles_property(self):
        """Свойство `roles` правильно определяет роли пользователя"""
        self.mock_launch.check_teacher_access.return_value = True
        self.mock_launch.check_teaching_assistant_access.return_value = False
        self.mock_launch.check_student_access.return_value = True

        user_service = UserService(self.mock_launch)
        user_roles = user_service.roles

        self.assertIn(UserRole.TEACHER, user_roles)
        self.assertIn(UserRole.STUDENT, user_roles)
        self.assertNotIn(UserRole.ASSISTANT, user_roles)
        self.assertEqual(len(user_roles), 2)

    def test_full_name_from_launch_data(self):
        """Имя берется из launch_data, NrpsService не используется"""
        self.mock_launch.get_launch_data.return_value = {
            "sub": "user-test-id",
            "name": "Alice from Launch"
        }

        user_service = UserService(self.mock_launch, nrps_service=self.mock_nrps)

        self.assertEqual(user_service.full_name, "Alice from Launch")
        self.mock_nrps.get_user_data.assert_not_called()

    def test_full_name_from_nrps_service(self):
        """Имени нет в launch_data, оно успешно берется из NRPS"""
        self.mock_nrps.get_user_data.return_value = NrpsUser(
            status="Active",
            name="Bob from NRPS",
            roles=["Student"]
        )

        user_service = UserService(self.mock_launch, nrps_service=self.mock_nrps)

        self.assertEqual(user_service.full_name, "Bob from NRPS")
        self.mock_nrps.get_user_data.assert_called_once_with("user-test-id")

    def test_full_name_is_none_if_not_in_launch_data_and_nrps_service_is_none(self):
        """Имени нет в launch_data, и NrpsService не был передан"""
        user_service = UserService(self.mock_launch, nrps_service=None)

        self.assertIsNone(user_service.full_name)

    def test_full_name_is_none_if_nrps_finds_nothing(self):
        """Имени нет в launch_data, и NrpsService ничего не находит"""
        self.mock_nrps.get_user_data.return_value = None

        user_service = UserService(self.mock_launch, nrps_service=self.mock_nrps)

        self.assertIsNone(user_service.full_name)
        self.mock_nrps.get_user_data.assert_called_once_with("user-test-id")
