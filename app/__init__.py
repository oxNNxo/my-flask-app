from flask import Flask
import logging

from config import Config
from app.datasource import db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=Config().LOGGING_LEVEL)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    # Initialize Flask extensions here

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app