import logging
import logging.handlers
import os
import requests
import time
import sys
from http import HTTPStatus
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
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(token_list)


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
        homework = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework.status_code != HTTPStatus.OK:
            logging.error('Сервер не отвечает')
            raise RequestError('Сервер не отвечает')
        else:
            return homework.json()
    except requests.exceptions.RequestException as error:
        logging.error('Эндпоит недоступен')
        raise RuntimeError(error)


def check_response(response):
    """Checks the API response for compliance with the documentation."""
    if not isinstance(response, dict):
        raise TypeError('Ответ не соответствет типу данных')
    elif 'current_date' not in response or 'homeworks' not in response:
        logging.error('Отсутствие ожидаемых ключей в ответе API')
        raise KeyError('Отсутствие ожидаемых ключей в ответе API')
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        raise TypeError('Список домашних работ не является списком')
    elif not homework:
        logging.debug('Список домашних работ пуст')
    return homework


def parse_status(homework):
    """Retrieves the task status from the homework information."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not homework_name:
        logging.error('Отсутствуют необходимые ключи в переданном словаре')
        raise KeyError('Отсутствуют необходимые ключи в переданном словаре')
    elif status not in HOMEWORK_VERDICTS:
        logging.error('Неожиданный статус домашней работы')
        raise UnexpectedStatusErorr('Неожиданный статус домашней работы')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """The basic logic of the work."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения.'
        )
        sys.exit(1)
    message_list = []

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
                    logging.debug('отсутствие в ответе новых статусов')
            else:
                logging.debug('Отсутствие в ответе новых статусов')
            timestamp = int(hw.get('current_date') - RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
