import os


class SecretsStore:
    """
    Хранилище секретов.
    Хранит связку ключ + nonce + timestamp, которая не должна повторяться при запросах.
    Nonce - одноразовый уникальный код для защиты запроса
    """
    def __init__(self):
        self.bunches = {}
        self.secrets = {}
        consumer_key = os.getenv("LTI_CONSUMER_KEY")
        secret_key = os.getenv("LTI_SECRET_KEY")

        if consumer_key and secret_key:
            self.secrets[consumer_key] = secret_key

    def get_secret(self, client_key: str):
        """
        Получить секретный ключ по ключу поставщика
        """
        return self.secrets.get(client_key, None)

    def save_bunch(self, client_key: str, nonce: str, timestamp: str):
        """
        Сохранить связку секретов
        """
        self.bunches[nonce] = (client_key, timestamp)

    def has_in_store(self, client_key: str, nonce: str, timestamp: str):
        """
        Проверить наличие связки в хранилище
        """
        return self.bunches.get(nonce) == (client_key, timestamp)
