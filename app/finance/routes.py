from flask import render_template

from app.finance import bp

@bp.route('/')
def index():
    return render_template('finance/index.html')
