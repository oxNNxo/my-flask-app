import requests
import logging
from flask import current_app

config = current_app.config

logger = logging.getLogger(__name__)

def lineNotifyMessage(msg,token):
    line_headers = {
        "Authorization": "Bearer " + token,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers = line_headers, params = payload)
    return r.status_code


def tgNotifyMessage(msg):
    bot_token = config['TELEGRAM_ALERT_TOKEN']
    chat_id = config['TELEGRAM_MY_CHAT_ROOM']
    text = msg
    url = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + chat_id + '&text=' + text
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0'}
    response = requests.get(url,headers = headers)
