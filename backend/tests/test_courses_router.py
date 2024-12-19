import unittest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi_another_jwt_auth import AuthJWT
from starlette.testclient import TestClient

from labstructanalyzer.routers.courses_router import router
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch

app = FastAPI()
app.include_router(router, prefix="/courses")
client = TestClient(app)


class TestUserRouter(unittest.TestCase):
    """Тестирование endpoints для работы с данными курсов."""

    @patch.object(AuthJWT, "jwt_required")
    @patch.object(AuthJWT, "get_raw_jwt")
    @patch.object(FastAPIMessageLaunch, "from_cache")
    def test_get_course_name_success(
            self,
            mock_message_launch_from_cache,
            mock_auth_jwt_get_raw_jwt,
            mock_auth_jwt_jwt_required
    ):
        """Тестирование успешного получения имени курса."""
        mock_auth_jwt_jwt_required.side_effect = None

        mock_auth_jwt_get_raw_jwt.return_value = {
            "launch_id": "test_launch_id",
        }
        mock_message_launch_instance = MagicMock()
        mock_message_launch_from_cache.return_value = mock_message_launch_instance
        mock_message_launch_instance.get_nrps.return_value.get_context.return_value = {"title": "Test Course"}

        response = client.get("/courses/current")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"name": "Test Course"}, response.json())

        mock_auth_jwt_jwt_required.assert_called_once()
        mock_auth_jwt_get_raw_jwt.assert_called_once()
        mock_message_launch_instance.get_nrps.assert_called_once()
        mock_message_launch_instance.get_nrps.return_value.get_context.assert_called_once()

    def test_get_course_user_not_found(self):
        """Тестирование получения имени курса для неавторизованного пользователя"""
        response = client.get("/courses/current")
        self.assertEqual(401, response.status_code)
        self.assertEqual(response.json(), {"detail": "Не авторизован"})
