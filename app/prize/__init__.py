from flask import Blueprint

bp = Blueprint('prize', __name__)

from app.prize import routes