from flask import render_template, request
import datetime
import logging

from app.ptt import bp, PttService
from app import LogService

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('ptt/index.html')


@bp.route('/articles', methods = ['GET', 'POST'])
def articles():
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        articles = PttService.get_articles_paginate(page, per_page)
    elif request.method == 'POST':
        board = request.values.get('board')
        author = request.values.get('author')
        title = request.values.get('title')
        startDate = request.values.get('startDate')
        endDate = request.values.get('endDate')
        articles = PttService.filter_article(constrains={'board':board,'author':author,'title':title,'startDate':startDate,'endDate':endDate})
    for article in articles:
        article.published = article.published.astimezone(datetime.timezone(datetime.timedelta(hours=+8))).strftime("%Y-%m-%d %H:%M:%S")
    return render_template('ptt/ptt_article.html', ptt_article = articles)


@bp.route('/filter')
def filter():
    initialData = PttService.initial_filter()
    return render_template('ptt/ptt_filter.html', initialData = initialData)

@bp.after_request
def log_request(response):
    return LogService.log_request(response,logger)
