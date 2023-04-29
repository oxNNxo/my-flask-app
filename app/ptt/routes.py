from flask import render_template
from app.ptt import bp

@bp.route('/')
def index():
    return render_template('ptt/index.html')
