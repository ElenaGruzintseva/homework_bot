# homework_bot

homework_bot - Телеграм бот для получения статуса проверки домашнего задания в Яндекс Практикум.

Стек технологий:

- Telebot

Чтобы развернуть проект клонируйте репозиторий:
```
https://github.com/ElenaGruzintseva/homework_bot
```

Перейдите в папку проекта:
```
cd homework_bot
```

Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
. venv/bin/activate
```

Установите зависимости:
```
pip install -r requirements.txt
```

Создайте файл .env и добавьте в него переменные окружения:
```
PRACTICUM_TOKEN = токен_Практикума
TELEGRAM_TOKEN = токен_телеграм_бота
TELEGRAM_CHAT_ID = токен_вашего_телеграма
```

Запустите проект:
```
python homework.py
```
