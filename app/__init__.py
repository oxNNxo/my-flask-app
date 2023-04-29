from flask import Flask

from config import Config
from app.datasource import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    # Initialize Flask extensions here

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.ptt import bp as ptt_bp
    app.register_blueprint(ptt_bp, url_prefix='/ptt')

    return app
