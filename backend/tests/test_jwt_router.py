import unittest
from fastapi.testclient import TestClient
from fastapi_another_jwt_auth import AuthJWT
from fastapi import FastAPI
from unittest.mock import patch

from fastapi_another_jwt_auth.exceptions import AuthJWTException

from labstructanalyzer.routers.jwt_router import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)


class TestJWTEndpoints(unittest.TestCase):

    """Тестирование endpoints для работы с токенами JWT."""

    @patch.object(AuthJWT, 'jwt_refresh_token_required')
    @patch.object(AuthJWT, 'get_jwt_subject')
    @patch.object(AuthJWT, 'get_raw_jwt')
    @patch.object(AuthJWT, 'create_access_token')
    def test_refresh_access_token_success(
            self,
            mock_create_access_token,
            mock_get_raw_jwt,
            mock_get_jwt_subject,
            mock_jwt_refresh_token_required,
    ):
        """Тестирование успешного обновления токена доступа."""
        mock_jwt_refresh_token_required.return_value = None
        mock_get_jwt_subject.return_value = "test_user"
        mock_get_raw_jwt.return_value = {"roles": "user", "launch_id": "123"}
        mock_create_access_token.return_value = "new_access_token"

        response = client.post("/refresh")
        self.assertEqual(200, response.status_code)
        self.assertEqual({"detail": "Обновлен токен доступа"}, response.json())
        self.assertEqual("new_access_token", response.cookies.get("access_token_cookie"))

        mock_jwt_refresh_token_required.assert_called_once()
        mock_get_jwt_subject.assert_called_once()
        mock_get_raw_jwt.assert_called_once()
        mock_create_access_token.assert_called_once_with(
            subject="test_user",
            user_claims={"roles": "user", "launch_id": "123"},
        )

    @patch.object(AuthJWT, 'jwt_refresh_token_required')
    def test_refresh_access_token_unauthorized(self, mock_jwt_refresh_token_required):
        """Тестирование неавторизованного обновления токена доступа."""
        mock_jwt_refresh_token_required.side_effect = AuthJWTException(401, "No token")

        response = client.post("/refresh")

        self.assertEqual(401, response.status_code)
        self.assertEqual({"detail": "Не авторизован"}, response.json())

        mock_jwt_refresh_token_required.assert_called_once()

    @patch.object(AuthJWT, 'unset_jwt_cookies')
    def test_logout_success(self, mock_unset_jwt_cookies,):
        """Тестирование успешного выхода из аккаунта."""
        mock_unset_jwt_cookies.return_value = None

        response = client.delete("/logout")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"detail": "Произведен выход из аккаунта"}, response.json())

        mock_unset_jwt_cookies.assert_called_once()