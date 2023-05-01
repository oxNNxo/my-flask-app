from flask import render_template, request
import datetime
import logging

from app.ptt import bp, PttService
from app import LogService

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('ptt/index.html')


@bp.route('/articles')
def articles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    articles = PttService.get_articles_paginate(page, per_page)
    for article in articles:
        article.published = article.published.astimezone(datetime.timezone(datetime.timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    return render_template('ptt/ptt_article.html', ptt_article=articles)


@bp.after_request
def log_request(response):
    return LogService.log_request(response,logger)
