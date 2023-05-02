from flask import Flask
import logging

from config import Config
from app.Extension import db

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=Config().LOGGING_LEVEL)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    with app.app_context():
        db.reflect()

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.ptt import bp as ptt_bp
    app.register_blueprint(ptt_bp, url_prefix='/ptt')

    return app
