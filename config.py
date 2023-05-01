import os

from dotenv import load_dotenv

load_dotenv()

class Config:

    FLASK_DEBUG_MODE = os.getenv('FLASK_DEBUG_MODE')

    SECRET_KEY = os.getenv('SECRET_KEY')

    DATABASE_HOST = os.getenv('DATABASE_HOST')
    DATABASE_NAME = os.getenv('DATABASE_NAME')
    DATABASE_USER = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}'

    LOGGING_LEVEL = int(os.getenv('LOGGING_LEVEL'))

    HOST = os.getenv('HOST')
    PORT = int(os.getenv('PORT', 5000))

    MYSELF_URL = os.getenv('MYSELF_URL')

    REURL_TOKEN1 = os.getenv('REURL_TOKEN1')
    REURL_TOKEN2 = os.getenv('REURL_TOKEN2')
    REURL_TOKEN3 = os.getenv('REURL_TOKEN3')

    TELEGRAM_ALERT_TOKEN = os.getenv('TELEGRAM_ALERT_TOKEN')
    TELEGRAM_MY_CHAT_ROOM = os.getenv('TELEGRAM_MY_CHAT_ROOM')