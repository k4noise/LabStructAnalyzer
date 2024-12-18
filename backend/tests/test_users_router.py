import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi_another_jwt_auth import AuthJWT

from labstructanalyzer.routers.users_router import router
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch

app = FastAPI()
app.include_router(router, prefix="/users")
client = TestClient(app)


class TestUserRouter(unittest.TestCase):
    """Тестирование endpoints для работы с пользователями."""

    @patch.object(AuthJWT, "jwt_required")
    @patch.object(AuthJWT, "get_raw_jwt")
    @patch.object(FastAPIMessageLaunch, "from_cache")
    def test_get_user_data_success(
            self,
            mock_message_launch_from_cache,
            mock_auth_jwt_get_raw_jwt,
            mock_auth_jwt_jwt_required
    ):
        """Тестирование успешного получения данных пользователя."""
        mock_auth_jwt_jwt_required.side_effect = None

        mock_auth_jwt_get_raw_jwt.return_value = {
            "sub": "test_user_id",
            "launch_id": "test_launch_id"
        }

        mock_message_launch_instance = MagicMock()
        mock_message_launch_from_cache.return_value = mock_message_launch_instance

        mock_message_launch_instance.get_iss.return_value = "http://test_lms_url"
        mock_message_launch_instance.get_nrps.return_value.get_context.return_value = {"title": "Test Course"}
        mock_message_launch_instance.get_nrps.return_value.get_members.return_value = [
            {"user_id": "test_user_id", "name": "Test User"}
        ]

        response = client.post("/users", headers={"Authorization": "Bearer test_token"})

        self.assertEqual(response.status_code, 200)
        expected_data = {
            "fullName": "Test User",
            "avatarUrl": "http://test_lms_url/user/pix.php/test_user_id/f1.jpg",
            "courseName": "Test Course"
        }
        self.assertEqual(response.json(), expected_data)

        mock_auth_jwt_jwt_required.assert_called_once()
        mock_auth_jwt_get_raw_jwt.assert_called_once()
        mock_message_launch_instance.get_iss.assert_called_once()
        mock_message_launch_instance.get_nrps.assert_called_once()
        mock_message_launch_instance.get_nrps.return_value.get_context.assert_called_once()
        mock_message_launch_instance.get_nrps.return_value.get_members.assert_called_once()

    def test_get_user_data_unauthorized(self):
        response = client.post("/users", headers={"Authorization": "Bearer invalid_token"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Не авторизован"})

    @patch.object(AuthJWT, "jwt_required")
    @patch.object(AuthJWT, "get_raw_jwt")
    @patch.object(FastAPIMessageLaunch, "from_cache")
    def test_get_user_data_user_not_found(
            self,
            mock_message_launch_from_cache,
            mock_auth_jwt_get_raw_jwt,
            mock_auth_jwt_jwt_required
    ):
        """Тестирование получения данных пользователя, если он не найден."""
        mock_auth_jwt_jwt_required.side_effect = None
        mock_auth_jwt_get_raw_jwt.return_value = {
            "sub": "test_user_id",
            "launch_id": "test_launch_id"
        }

        mock_message_launch_instance = MagicMock()
        mock_message_launch_from_cache.return_value = mock_message_launch_instance

        mock_message_launch_instance.get_iss.return_value = "test_lms_url"
        mock_message_launch_instance.get_nrps.return_value.get_context.return_value = {"title": "Test Course"}
        mock_message_launch_instance.get_nrps.return_value.get_members.return_value = [
            {"user_id": "other_user_id", "name": "Other User"}
        ]

        response = client.post("/users", headers={"Authorization": "Bearer test_token"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Пользователь не найден"})

        mock_auth_jwt_jwt_required.assert_called_once()
        mock_auth_jwt_get_raw_jwt.assert_called_once()
        mock_message_launch_instance.get_iss.assert_called_once()
        mock_message_launch_instance.get_nrps.assert_called_once()
        mock_message_launch_instance.get_nrps.return_value.get_context.assert_called_once()
        mock_message_launch_instance.get_nrps.return_value.get_members.assert_called_once()
