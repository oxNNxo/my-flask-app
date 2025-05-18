from flask import render_template
import logging

from app.store import bp
from app import LogService

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('store/index.html')

@bp.after_request
def log_request(response):
    return LogService.log_request(response,logger)