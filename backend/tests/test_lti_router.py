import unittest

from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi_another_jwt_auth import AuthJWT
from pylti1p3.exception import OIDCException, LtiException
from unittest.mock import patch, MagicMock

from labstructanalyzer.services.pylti1p3.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.pylti1p3.oidc_login import FastAPIOIDCLogin
from labstructanalyzer.routers.lti_router import router as lti_router
from labstructanalyzer.services.lti.user import User


class TestLoginRoute(unittest.TestCase):
    """
    Тестовый класс для проверки маршрута /lti/login.
    """

    def setUp(self):
        """
        Инициализация тестового клиента и настройка маршрутизатора перед каждым тестом.
        """
        self.app = FastAPI()
        self.app.include_router(lti_router, prefix="/lti")
        self.client = TestClient(self.app)
        self.target_link_uri = "http://example.com/target_link_uri"

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_get_request(self, mock_redirect):
        """
        Тестирует GET-запрос к маршруту /lti/login с корректным параметром target_link_uri.
        Ожидается успешный ответ со статусом 200.
        """
        mock_redirect.return_value = None
        response = self.client.get("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(200, response.status_code)
        mock_redirect.assert_called_once_with(self.target_link_uri)

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_post_request(self, mock_redirect):
        """
        Тестирует POST-запрос к маршруту /lti/login с корректным параметром target_link_uri.
        Ожидается успешный ответ со статусом 200.
        """
        mock_redirect.return_value = None
        response = self.client.post("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(200, response.status_code)
        mock_redirect.assert_called_once_with(self.target_link_uri)

    def test_login_missing_target_link_uri(self):
        """
        Тестирует GET-запрос к маршруту /lti/login без параметра target_link_uri.
        Ожидается ответ с ошибкой 400 и соответствующим сообщением.
        """
        response = self.client.get("/lti/login")
        self.assertEqual(400, response.status_code)
        self.assertEqual('{"detail":"Отсутствует параметр \\"target_link_uri\\""}', response.text)

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_oidc_exception(self, mock_redirect):
        """
        Тестирует обработку исключения OIDCException при запросе к маршруту /lti/login.
        Ожидается ответ с ошибкой 500 и соответствующим сообщением.
        """
        mock_redirect.side_effect = OIDCException
        response = self.client.get("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(500, response.status_code)
        self.assertEqual('{"detail":"Вход не выполнен, попробуйте ещё раз"}', response.text)
        mock_redirect.assert_called_once_with(self.target_link_uri)


class TestLaunchRoute(unittest.TestCase):
    """
    Тестовый класс для проверки маршрута /lti/launch.
    """

    def setUp(self):
        """
        Инициализация тестового клиента и настройка маршрутизатора перед каждым тестом.
        """
        self.app = FastAPI()
        self.app.include_router(lti_router, prefix="/lti")
        self.client = TestClient(self.app)

    @patch.object(FastAPIMessageLaunch, 'validate_registration')
    def test_launch_lti_exception(self, mock_message_launch):
        """
        Тестирует обработку исключения LtiException при запросе к маршруту /lti/launch.
        Ожидается ответ с ошибкой 500 и соответствующим сообщением.
        """
        mock_message_launch.side_effect = LtiException
        response = self.client.post("/lti/launch")
        self.assertEqual('{"detail":"Ошибка регистрации внешнего инструмента"}', response.text)
        self.assertEqual(500, response.status_code)
        mock_message_launch.assert_called_once()

    @patch.multiple(FastAPIMessageLaunch,
                    validate_registration=MagicMock(return_value=True),
                    get_launch_data=MagicMock(return_value={"sub": "localhost"}),
                    get_launch_id=MagicMock(return_value=123))
    @patch.multiple(AuthJWT,
                    create_access_token=MagicMock(return_value="access"),
                    create_refresh_token=MagicMock(return_value="refresh"),
                    )
    @patch.object(User, 'get_role', return_value=["student"])
    def test_launch_right(self, mock_get_role):
        """
        Тестирует успешный запуск LTI-запроса к маршруту /lti/launch.
        Ожидается перенаправление (статус 302) и установка соответствующих cookie.
        """
        response = self.client.post("/lti/launch", allow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertEqual("access", response.cookies.get("access_token_cookie"))
        self.assertEqual("refresh", response.cookies.get("refresh_token_cookie"))
        self.assertEqual("/templates", response.headers.get("location"))

        FastAPIMessageLaunch.validate_registration.assert_called_once()
        FastAPIMessageLaunch.get_launch_data.assert_called_once()
        FastAPIMessageLaunch.get_launch_id.assert_called_once()
        AuthJWT.create_access_token.assert_called_once_with(subject="localhost", user_claims={"roles": ["student"], "launch_id": 123})
        AuthJWT.create_refresh_token.assert_called_once_with(subject="localhost", user_claims={"roles": ["student"], "launch_id": 123})
        mock_get_role.assert_called_once()


if __name__ == '__main__':
    unittest.main()