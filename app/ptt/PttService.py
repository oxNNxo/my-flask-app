import requests
import datetime
from bs4 import BeautifulSoup
import re
import time
import logging
from flask import current_app
import uuid
from sqlalchemy import and_

from app.models.ptt import User, Board, Article, Subs, UserSubs, SubsArticle
from app import CommonService
from app import MessageService


config = current_app.config
db = current_app.extensions['sqlalchemy']

logger = logging.getLogger(__name__)

tzTaipei = datetime.timezone(datetime.timedelta(hours=+8))

token_reurl = config['REURL_TOKEN']

def get_articles_paginate(page = 1, per_page = 10):
    all_results = (
        Article
        .query
        .order_by(Article.published.desc())
        .paginate(page=page,per_page=per_page,max_per_page=100,error_out=False)
        )
    return all_results


def get_board_with_subs():
    all_results = (
        db.session
        .query(Board,Subs,User)
        .filter(UserSubs.subs_id==Subs.id)
        .filter(Subs.board==Board.board)
        .filter(User.id==UserSubs.user_id)
        .all()
        )
    return all_results


def crawl_ptt(board):
    url =  'https://www.ptt.cc/atom/' + board + '.xml'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0'}
    response = requests.get(url,headers = headers)
    soup = BeautifulSoup(response.content,'html.parser')
    articlelist = list()
    for entry in soup.find_all('entry') :
        title = entry.find('title').text
        link = entry.find('link')['href']
        author = entry.find('author').find('name').text
        published = entry.find('published').text
        content = entry.find('content').text.strip('<pre> ').strip('\n</pre>')
        article = Article(board=board, author=author, title=title, link=link, content=content,
            published=datetime.datetime.strptime(published,'%Y-%m-%dT%H:%M:%S%z'), id=uuid.uuid4())
        articlelist.append(article) # new to old
    logger.info(f"{'{:<12}'.format(board)} {articlelist[0].published}")
    return articlelist


def update_pyptt_board_latest_time(boardDict):
    for board, boardInfo in boardDict.items():
        board.latest_time = boardInfo['article'][0].published
    return


def update_pyptt_article(article_list):
    for article in article_list:
        db.session.add(article)
    return

def update_subs_article(subs_article):
    for subs, article in subs_article:
        db.session.add(SubsArticle(subs_id=subs.id,article_id=article.id))
    return

def notify_subs_article(articleList,user):
    newfeed_article = list()
    for article in articleList:
        newfeed_article.append('{:<12}'.format(article.board) + ' ' + article.link + '\n' + article.title)# board link <br> title
    while len(newfeed_article) > 0:
        newline_chara = '\n'
        msg_user = f"```{newline_chara.join(newfeed_article[:10])}```"
        MessageService.lineNotifyMessage(msg_user,user.chat_id)
        newfeed_article = newfeed_article[10:]
    return


def filter_article(constrains = dict(), page = 1, per_page = 10):
    ands = list()
    for column,value in constrains.items():
        if value == '':
            continue
        if column == 'board':
            ands.append(and_(Article.board==value))
        elif column == 'author':
            ands.append(and_(Article.author.contains(value)))
        elif column == 'title':
            ands.append(and_(Article.title.ilike(f'%{value}%')))
        elif column == 'startDate':
            ands.append(and_(Article.published >= datetime.datetime.strptime(value + " 00:00:00", "%Y/%m/%d %H:%M:%S").astimezone(tzTaipei)))
        elif column == 'endDate':
            ands.append(and_(Article.published <= datetime.datetime.strptime(value + " 23:59:59", "%Y/%m/%d %H:%M:%S").astimezone(tzTaipei)))
    return (Article.query.filter(*ands).order_by(Article.published.desc())
        .paginate(page=page,per_page=per_page,max_per_page=100,error_out=False))


def initial_filter():
    Board_list = Board.query.order_by(Board.board).all()
    return {'board':Board_list}


def delete_old_articles(days):
    logger.info(f'delete old articles before {days} days ago')
    delete_days_range = (datetime.datetime.now() - datetime.timedelta(days = days)).astimezone(datetime.timezone.utc)
    subsarticles = (
                    SubsArticle
                    .query
                    .join(Article,Article.id == SubsArticle.article_id)
                    .filter(Article.published < delete_days_range)
                    .order_by(Article.published.desc())
                    .all()
                    )
    logger.info(subsarticles)
    for subarticle in subsarticles:
        db.session.delete(subarticle)
    db.session.commit()
    articles = (
                Article.query
                .filter(Article.published < delete_days_range)
                .order_by(Article.published.desc())
                .all()
                )
    logger.info(articles)
    for article in articles:
        db.session.delete(article)
    db.session.commit()
    logger.info('articles deleted successfully')



def check_ptt_newfeed():
    logger.info('Checking for ptt newfeed')
    board_with_user = get_board_with_subs()
    boardDict = {
        pair1[0]:{
            'subs':list(dict.fromkeys([
                pair2[1] for pair2 in board_with_user if pair1[0]==pair2[0] and pair2[1]
            ])),
            'article':[]
        }
        for pair1 in board_with_user
    }
    userDict = {
        pair1[2]:[
                pair2[1] for pair2 in board_with_user if pair1[2]==pair2[2]
        ]
        for pair1 in board_with_user
    }
    try:
        to_update_pyptt_article = list()
        subs_article = list()
        for board, boardInfo in boardDict.items():
            boardInfo['article'] = crawl_ptt(board.board)
            latestTime = board.latest_time
            _minute = latestTime.time().minute
            if  _minute >= 0 and _minute < 20 :
                token = token_reurl[0]
            elif _minute >= 20 and _minute < 40 :
                token = token_reurl[1]
            elif _minute >= 40 and _minute < 60 :
                token = token_reurl[2]
            for article in reversed(boardInfo['article']) : # old to new
                if article.published > latestTime:
                    for subs in boardInfo['subs']:
                        _pattern = re.compile(subs.sub_key,flags=re.IGNORECASE)
                        if re.search(_pattern,article.title) :
                            if 'reurl.cc' not in article.link:
                                article.link = CommonService.reurl(token,article.link)
                            subs_article.append((subs, article))
                            if article not in to_update_pyptt_article:
                                to_update_pyptt_article.append(article)
        for user, userSubs in userDict.items():
            newfeed_article = list()
            for subs, article in subs_article:
                if subs in userSubs and article not in newfeed_article:
                    newfeed_article.append(article)
            notify_subs_article(newfeed_article, user)
            
    except IndexError:
        logger.error(str(IndexError))
        pass
    except requests.exceptions.ConnectionError:
        logger.error(str(requests.exceptions.ConnectionError))
        pass
    except requests.exceptions.SSLError:
        logger.error(str(requests.exceptions.SSLError))
        pass
    except Exception as e:
        logger.error(str(e))
        pass

    try:
        update_pyptt_board_latest_time(boardDict)
        update_pyptt_article(to_update_pyptt_article)
        update_subs_article(subs_article)
        db.session.commit()
        logger.info('Update ptt newfeed successfully')
    except Exception as e:
        MessageService.tgNotifyMessage(f'{__name__} - Update PyPTT board list error:{e}')
        logger.error(str(e))
        db.session.rollback()
    logger.info('Checking for ptt newfeed successfully')
