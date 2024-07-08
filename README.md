# fast-chess_prod

Для запуска введите:

python -m venv venv

venv\scripts\activate.bat
(для Windows)

pip install -r requirements.txt

зарегистрируйтесь и создайте диалог на платформе https://dialogs.yandex.ru/developer/

идентификатор диалога введите в переменную SKILL в файле REFERENCES

получите персональный OAuth-токен для диалогов по ссылке из пункта документации "Авторизация" https://yandex.ru/dev/dialogs/alice/doc/ru/resource-upload#auth

персональный OAuth-токен введите в переменную TOKEN в файле REFERENCES

введите в терминал

python main.py

запустите ngrok и введите

ngrok http 5000

полученную ссылку введите, как Webhook URL в разделе "Настройки" созданного диалога

нажмите сохранить и перейдите в раздел "Тестирование" и пользуйтесь!

