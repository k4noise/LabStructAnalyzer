## Общая часть для любой LMS:

В меню настройки инструмента LTI укажите следующие настройки, предварительно заменив <tool url> на URL инструмента (URL реверс-прокси или бэкенда):
- Tool URL: \<tool url>/api/v1/lti/launch
- LTI version: LTI 1.3
- Public key type: Keyset URL
- Public keyset: \<tool url>/api/v1/lti/jwks
- Initiate login URL: \<tool url>/api/v1/lti/login
- Redirection URI(s): \<tool url>/api/v1/lti/launch

И включите следующие сервисы:
- Deep Linking
- IMS LTI Assignment and Grade Services (AGS) - Use this service for grade sync and column management
- IMS LTI Names and Role Provisioning (NRPS) - Use this service to retrieve members' information as per privacy settings

## Часть для Moodle

Все действия по созданию и настройке инструмента выполняются в режиме редактирования внутри курса. 

### Для версий Moodle 4.1.14 и ниже элемент создается следующим образом: 
<img src="https://i.imgur.com/ztHiLY5.png">
<img src="https://i.imgur.com/aICFdHm.png">
Откроется меню настроек инструмента, укажите все вышеперечисленные данные.

### Для новых версий Moodle:
Создание инструмента:

<img src="https://i.imgur.com/dpK5sYo_d.webp?maxwidth=360&fidelity=grand">
<img src="https://i.imgur.com/gPp8aau_d.webp?maxwidth=760&fidelity=grand">
Добавление в курс:
<img src="https://i.imgur.com/Q1ZouSI_d.webp?maxwidth=760&fidelity=grand">


### Для всех версий Moodle (продолжение):
Обязательно укажите принудительную настройку `Share launcher's name with tool` как `Always`

После того, как настройки отдельного инструмента будут завершены, укажите название элемента и проверьте правильность настроек по образцу ниже.

<img src="https://i.imgur.com/D197hfr_d.webp?maxwidth=540&fidelity=grand">

После сохранения инструмента сформируются `client_id` и `deplyment_id`.

Для администратора: Site administration - Plugins - External tool - Manage tools - View configuration details.

Для учителя `client_id` можно узнать в настройках инструмента, а `deployment_id` только из параметра `typeid` URL настройки инструмента.

Если при запуске возникает ошибка, вернитесь к настройкам инструмента LTI и замените `Public key type` на `RSA key`, скопируйте в поле `Public key` содержимое jwtRS256.key.pub.