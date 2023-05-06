from flask import render_template

from app.prize import bp

@bp.route('/')
def index():
    return render_template('prize/index.html')
