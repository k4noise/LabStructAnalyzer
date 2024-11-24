from oauthlib.oauth1 import RequestValidator

from labstructanalyzer.config import Settings
from labstructanalyzer.services.secrets_store import SecretsStore

secrets_store = SecretsStore()


class LTIRequestValidator(RequestValidator):
    """
    Валидатор запроса LTI
    """

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    @property
    def client_key_length(self):
        return 15, 40

    @property
    def nonce_length(self):
        return 20, 40

    @property
    def enforce_ssl(self):
        return False

    def get_client_secret(self, client_key, request) -> str:
        return secrets_store.get_secret(client_key) or "dummy"

    def validate_client_key(self, client_key, request) -> bool:
        return bool(secrets_store.get_secret(client_key))

    def validate_timestamp_and_nonce(
            self,
            client_key,
            timestamp,
            nonce,
            request,
            request_token=None,
            access_token=None,
    ):
        has_in_store = secrets_store.has_in_store(client_key, nonce, timestamp)
        if has_in_store:
            raise ValueError("Связка nonce, client_key и timestamp не уникальна")

        secrets_store.save_bunch(client_key, nonce, timestamp)
        return True

    def dummy_client(self):
        return "dummy_client"
