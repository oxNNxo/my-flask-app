from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from flask_jwt_extended import JWTManager
jwt = JWTManager()
from flask_apscheduler import APScheduler
scheduler = APScheduler()