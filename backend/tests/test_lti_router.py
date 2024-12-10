import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi_another_jwt_auth import AuthJWT
from fastapi_another_jwt_auth.exceptions import AuthJWTException
from pylti1p3.exception import OIDCException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from unittest.mock import patch, MagicMock, AsyncMock

from labstructanalyzer.services.lti.cache import FastAPICacheDataStorage
from labstructanalyzer.services.lti.message_launch import FastAPIMessageLaunch
from labstructanalyzer.services.lti.oidc_login import FastAPIOIDCLogin
from pylti1p3.tool_config import ToolConfJsonFile
from labstructanalyzer.configs.config import LTI_CONFIG_FILE_PATH
from labstructanalyzer.routers.lti_router import router as lti_router
from labstructanalyzer.services.lti.roles import LTIRoles


class TestLoginRoute(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(lti_router)
        self.client = TestClient(self.app)
        self.tool_conf = ToolConfJsonFile(LTI_CONFIG_FILE_PATH)
        FastAPICache.init(InMemoryBackend())
        cache = FastAPICache.get_backend()
        self.launch_data_storage = FastAPICacheDataStorage(cache)
        self.target_link_uri = "http://example.com/target_link_uri"

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_get_request(self, mock_redirect):
        mock_redirect.return_value = None
        response = self.client.get("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(response.status_code, 200)

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_post_request(self, mock_redirect):
        mock_redirect.return_value = None
        response = self.client.post("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(response.status_code, 200)

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_missing_target_link_uri(self):
        response = self.client.get("/lti/login")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.text, 'Нет параметра "target_link_uri"')

    @patch.object(FastAPIOIDCLogin, 'redirect')
    def test_login_oidc_exception(self, mock_redirect):
        mock_redirect.side_effect = OIDCException
        response = self.client.get("/lti/login", params={"target_link_uri": self.target_link_uri})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, 'Error doing OIDC login')


if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()