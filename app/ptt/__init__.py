from flask import Blueprint

bp = Blueprint('ptt', __name__)

from app.ptt import routes