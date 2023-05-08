from flask import Flask
import logging

from config import Config
from app.Extension import db, jwt, scheduler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=Config().LOGGING_LEVEL)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    with app.app_context():
        db.reflect()
    jwt.init_app(app)
    scheduler.init_app(app)
    
    # Register blueprints here
    with app.app_context():
        
        from app.main import bp as main_bp
        app.register_blueprint(main_bp)

        from app.ptt import bp as ptt_bp
        app.register_blueprint(ptt_bp, url_prefix='/ptt')

        from app.finance import bp as finance_bp
        app.register_blueprint(finance_bp, url_prefix='/finance')

        from app import SchedulerService

    scheduler.start()

    return app
