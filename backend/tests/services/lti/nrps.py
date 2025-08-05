import unittest
from unittest.mock import MagicMock, patch

from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.exceptions.lis_service_no_access import NrpsNotSupportedException
from labstructanalyzer.schemas.user import NrpsUser  # Ваша Pydantic-модель


class TestNrpsService(unittest.TestCase):

    def setUp(self):
        self.valid_user_data_list = [
            {
                "user_id": "user-001",
                "name": "Alice",
                "status": "Active",
                "roles": ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"]
            },
            {
                "user_id": "user-002",
                "name": "Bob",
                "status": "Active",
                "roles": ["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"]
            }
        ]

        self.mock_message_launch = MagicMock()
        self.mock_message_launch.has_nrps.return_value = True
        self.mock_message_launch.get_nrps.return_value.get_members.return_value = self.valid_user_data_list

    def test_init_raises_exception_if_nrps_not_supported(self):
        """Сервис должен выбросить исключение, если NRPS не поддерживается"""
        self.mock_message_launch.has_nrps.return_value = False

        with self.assertRaises(NrpsNotSupportedException):
            NrpsService(self.mock_message_launch)

    def test_get_user_by_id_success(self):
        """Сервис находит пользователя и возвращает валидную модель"""
        service = NrpsService(self.mock_message_launch)
        user = service.get_user_by_id("user-001")

        self.assertIsNotNone(user)
        self.assertIsInstance(user, NrpsUser)
        self.assertEqual(user.name, "Alice")
        self.assertEqual(user.status, "Active")

    def test_get_user_by_id_returns_none_for_nonexistent_user(self):
        """Сервис возвращает None, если пользователь не найден"""
        service = NrpsService(self.mock_message_launch)
        user = service.get_user_by_id("user-999-non-existent")

        self.assertIsNone(user)

    def test_api_is_called_only_once_due_to_caching(self):
        """Внешний API вызывается только один раз"""
        service = NrpsService(self.mock_message_launch)

        service.get_user_by_id("user-001")
        service.get_user_by_id("user-002")
        service.get_user_by_id("user-001")

        self.mock_message_launch.get_nrps.return_value.get_members.assert_called_once()

    def test_service_is_robust_to_invalid_data_from_api(self):
        """Сервис не падает из-за невалидных данных, а пропускает их"""
        mixed_data = [
            {
                "user_id": "user-valid-1",
                "name": "Valid User",
                "status": "Active",
                "roles": []
            },
            {
                "user_id": "user-invalid-1",
                "name": "Invalid User",
                # "status" отсутствует, Pydantic должен выдать ошибку
                "roles": []
            }
        ]
        self.mock_message_launch.get_nrps.return_value.get_members.return_value = mixed_data
        service = NrpsService(self.mock_message_launch)

        valid_user = service.get_user_by_id("user-valid-1")
        self.assertIsNotNone(valid_user)
        self.assertEqual(valid_user.name, "Valid User")

        invalid_user = service.get_user_by_id("user-invalid-1")
        self.assertIsNone(invalid_user)
