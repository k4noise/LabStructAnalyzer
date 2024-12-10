## Как запустить:

Важно! Не используйте описанные команды запуска системы на продакшене! <br>
Используйте **только** для локального исследования возможностей системы!

## Перед запуском:

Система работает только по HTTPS. Для этого сгенерируйте сертификат и ключ (или используйте существующие `cert.pem` и `key.pem`):
`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=CompanySectionName/CN=CommonNameOrHostname"`

### Бэкенд

0. Перейти в папку `backend`
1. Переименовать `.env.example` в `.env`, изменить необходимые значения
2. В папке `labstructanalyzer/configs` переименовать `lti_config.json.example` в `lti_config.json` и изменить `http://moodle_external_lms_url` на URL развернутой Moodle
3. В папке `labstructanalyzer/configs` сгенерируйте ключи самостоятельно:

```
ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
# Don't add passphrase
openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
```

ИЛИ создайте файлы `jwtRS256.key` и `jwtRS256.key.pub` вручную и
поместите в них копии содержимого с [этого сайта](https://lti-ri.imsglobal.org/keygen/index). <br>
В файл `jwtRS256.key` поместите содержимое, которое начинается с `-----BEGIN RSA PRIVATE KEY-----`,
в файл `jwtRS256.key.pub` поместите содержимое, которое начинается с `-----BEGIN PUBLIC KEY-----`.

4. Установить `poetry`, если не установлен: `pip install poetry`
5. Установить зависимости проекта: `poetry install`
6. Запустить проект: `poetry run dev`

### Фронтенд

0. Перейти в папку `frontend`
1. Установить `nodejs` с [офиц. сайта](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) или через пакетные менеджеры, если не установлен
1. Установить зависимости проекта: `npm install`
1. Запустить проект: `npm run dev`
