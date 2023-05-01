from flask import render_template
import logging

from app.main import bp
from app import LogService

logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.after_request
def log_request(response):
    return LogService.log_request(response,logger)
