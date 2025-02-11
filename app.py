import hashlib
import json
import os
import uuid
import requests
from dotenv import load_dotenv
from flask import Flask, request, render_template
import logging

logger = logging.Logger(__name__)

load_dotenv()
app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", 'gfdmhghif38yrf9ew0jkf32')
URL = os.getenv("URL", 'gfdmhghif38yrf9ew0jkf32')


def generate_signature(data: dict) -> hashlib:
    """
    Функция для генерации sha256-хэша принятого словаря

    :param data: Словарь с данными
    :return: хэшированное значение
    """
    # Сортируем данные по ключам и конкатенируем их
    concatenated_string = ''.join(
        str(data[key]) for key in sorted(data.keys())
    ) + SECRET_KEY
    # Генерируем SHA256 хеш
    return hashlib.sha256(concatenated_string.encode()).hexdigest()


def send_payment(data: dict) -> request:
    """
    Функция отправки POST запроса с данными транзакции

    :param data: Словарь с данными
    :return: HTTP response
    """
    logger_text = f"Trying to send probes: {data} ... "
    logger.info(logger_text)
    response = requests.post(
        url=URL,
        headers={'Content-type': 'application/json'},
        data=json.dumps({'transaction_id': data['transaction_id'],
                         'user_id': data['user_id'],
                         'account_id': data['account_id'],
                         'amount': data['amount'],
                         'signature': data['signature'],
                         }),
        timeout=100,
    )
    if response.status_code == 200:
        logger_text += "Success!"
        logger.info(logger_text)
    else:
        logger_text += f"{response.content.decode()}!"
        logger.error(logger_text)

    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Основная функция обработки корневого адреса (эндпоинта) страницы

    :param user_id: id пользователя (из формы на отправку)
    :param account_id: id счета пользователя (из формы на отправку)
    :param amount: сумма платежа (из формы на отправку)
    :return: HTML-страница
    """
    context = {}
    if request.method == 'POST':
        received_data = {"user_id": int(request.form.get('user_id')),
                         "account_id": int(request.form.get('account_id')),
                         "amount": int(request.form.get('amount'))}
        logger.warning(f"user_id: {received_data['user_id']}, "
                       f"account_id: {received_data['account_id']}, "
                       f"amount: {received_data['amount']}")
        transaction_id = str(uuid.uuid4())
        logger.warning(f"generated transaction_id: {transaction_id}")
        received_data['transaction_id'] = transaction_id
        signature = str(generate_signature({'transaction_id': received_data['transaction_id'],
                                            'user_id': received_data['user_id'],
                                            'account_id': received_data['account_id'],
                                            'amount': received_data['amount'],
                                            }))
        logger.warning(f"generated signature: {signature}")
        received_data['signature'] = signature
        response = send_payment(received_data)
        context = {'transaction_id': transaction_id,
                   'user_id': received_data['user_id'],
                   'account_id': received_data['account_id'],
                   'amount': received_data['amount'],
                   'signature': signature,
                   'status_code': response.status_code,
                   'status_result': list(json.loads(response.content.decode()).items())[0][0],
                   'status_content': list(json.loads(response.content.decode()).items())[0][1],
                   }

    return render_template('index.html', **context)


if __name__ == '__main__':
    app.run(port=5000)
