import logging
import logging.handlers
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import RequestError, UnexpectedStatusErorr

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Checks the availability of environment variables."""
    missing_tokens = []
    if not PRACTICUM_TOKEN:
        missing_tokens.append('PRACTICUM_TOKEN')
    if not TELEGRAM_TOKEN:
        missing_tokens.append('TELEGRAM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        missing_tokens.append('TELEGRAM_CHAT_ID')
    if missing_tokens:
        for token in missing_tokens:
            logging.critical(f'Отсутствует обязательная переменная: {token}')
        return False
    return True


def send_message(bot, message):
    """Sending messages to the Telegram chat."""
    try:
        logging.info('Начало отправки сообщения')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено')
    except Exception:
        logging.error('Сбой при отправке сообщения')


def get_api_answer(timestamp):
    """Makes a request to the endpoint of the API service."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.exceptions.RequestException as error:
        raise RuntimeError(f'Эндпоит недоступен: {error}')
    if response.status_code != HTTPStatus.OK:
        raise RequestError(
            f'Сервер не отвечает, статус: {response.status_code}'
        )
    return response.json()


def check_response(response):
    """Checks the API response for compliance with the documentation."""
    if not isinstance(response, dict):
        raise TypeError(f"Ответ не соответствет типу данных: {type(response)}")
    if 'current_date' not in response:
        raise KeyError("Ключ 'current_date' отсутствует в ответе API")
    if 'homeworks' not in response:
        raise KeyError("Ключ 'homeworks' отсутствует в ответе API")
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError(
            f"Список домашних работ не является списком: {type(homework)}"
        )
    return homework


def parse_status(homework):
    """Retrieves the task status from the homework information."""
    if 'homework_name' not in homework:
        raise KeyError("Ключ 'homework_name' отсутствует в переданном словаре")
    if 'status' not in homework:
        raise KeyError("Ключ 'status' отсутствует в переданном словаре")
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise UnexpectedStatusErorr(
            f"Неожиданный статус домашней работы: {status}"
        )
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """The basic logic of the work."""
    if not check_tokens():
        logging.critical(
            'Отсутствуют обязательные переменные окружения.'
        )
        sys.exit(1)
    bot = TeleBot(token=TELEGRAM_TOKEN)
    message_list = []
    timestamp = int(time.time())
    while True:
        try:
            hw = get_api_answer(timestamp)
            hw_list = check_response(hw)
            if hw_list:
                message = parse_status(hw_list[0])
                if message not in message_list:
                    message_list.clear()
                    message_list.append(message)
                    send_message(bot, message)
                else:
                    logging.debug('Отсутствие в ответе новых статусов')
            else:
                logging.debug('Отсутствие в ответе новых статусов')
            timestamp = int(hw.get('current_date') - RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
