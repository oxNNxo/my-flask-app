import requests
import datetime
from bs4 import BeautifulSoup
import re
import time
import logging
from flask import current_app

from app.models.ptt import User, Board, Article, Subs, UserSubs
from app import CommonService
from app import MessageService


config = current_app.config
db = current_app.extensions['sqlalchemy']

logger = logging.getLogger(__name__)

token_reurl = config['REURL_TOKEN']

def get_articles_paginate(page, per_page):
    return Article.query.order_by(Article.published.desc()).paginate(page=page,per_page=per_page,max_per_page=100,error_out=False)


def get_pyptt_user_subs_board_with_latest_time():
    all_results = (
                    Board
                    .query
                    .join(Subs, Subs.board == Board.board)
                    .join(UserSubs, UserSubs.subs_id == Subs.id)
                    .distinct()
                    .all()
                    )
    return all_results


def get_pyptt_user_board_key():
    all_results = (
                    db.session
                    .query(User, Subs)
                    .join(UserSubs, UserSubs.subs_id == Subs.id)
                    .join(User, User.id == UserSubs.user_id)
                    .distinct()
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
        corr_time = str(published[:10]) + ' ' + str(published[11:19])
        article = Article(board=board, author=author, title=title, link=link, content=content,
            published=datetime.datetime.strptime(corr_time,'%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone(datetime.timedelta(hours=+8))))
        articlelist.append(article) # new to old
    logger.info(f"{'{:<12}'.format(board)} {articlelist[0].published}")
    return articlelist


def update_pyptt_board_latest_time(blt_list):
    for blt in blt_list:
        (
            db.session
            .query(Board)
            .filter(Board.board == blt['board'])
            .update({Board.latest_time: blt['latest_time']})
            )
    db.session.commit()
    return


def update_pyptt_article(article_list):
    for article in article_list:
        article_dict = article.__dict__
        article_dict.pop('_sa_instance_state')
        insert_stmt = db.dialects.postgresql.insert(Article).values(article_dict)
        update_stmt = insert_stmt.on_conflict_do_update(constraint="article_unique",set_=dict(link=article.link))
        db.session.execute(update_stmt)
    db.session.commit()


def check_ptt_newfeed():
    logger.info('Checking for ptt newfeed')
    board_latest_time = get_pyptt_user_subs_board_with_latest_time()
    logger.debug(board_latest_time)
    blt = dict()
    for board in board_latest_time:
        blt[board.board] = dict()
        blt[board.board]['pre_latest_time'] = board.latest_time.astimezone(datetime.timezone(datetime.timedelta(hours=+8)))
    logger.debug(blt)
    user_board_key_list = get_pyptt_user_board_key()
    logger.debug(user_board_key_list)
    ubk = dict()
    for user, subs in user_board_key_list:
        if user not in ubk:
            ubk[user] = dict()
        if subs.board not in ubk[user]:
            ubk[user][subs.board] = list()
        ubk[user][subs.board].append(subs.sub_key)
    logger.debug(ubk)
    try:
        for boardName in blt:
            blt[boardName]['article'] = crawl_ptt(boardName)
            blt[boardName]['now_latest_time'] = blt[boardName]['article'][0].published
            time.sleep(1)
        to_update_pyptt_article = list()
        for user in ubk:
            newfeed_article = list()
            for boardName in ubk[user]:
                latesttime = blt[boardName]['pre_latest_time']
                _minute = latesttime.time().minute
                if  _minute >= 0 and _minute < 20 :
                    token = token_reurl[0]
                elif _minute >= 20 and _minute < 40 :
                    token = token_reurl[1]
                elif _minute >= 40 and _minute < 60 :
                    token = token_reurl[2]
                for article in reversed(blt[boardName]['article']) : # old to new
                    if article.published > latesttime:
                        for pattern in ubk[user][boardName]:
                            _pattern = re.compile(pattern,flags=re.IGNORECASE)
                            if re.search(_pattern,article.title) :
                                if 'reurl.cc' not in article.link:
                                    article.link = CommonService.reurl(token,article.link)
                                time.sleep(3)
                                newfeed = 1
                                morefeed = 1
                                newfeed_article.append('{:<12}'.format(boardName) + ' ' + article.link + '\n' + article.title)    # board link <br> title
                                to_update_pyptt_article.append(article)
                                break
            while len(newfeed_article) > 0:
                newline_chara = '\n'
                msg_user = f"```{newline_chara.join(newfeed_article[:10])}```"
                MessageService.lineNotifyMessage(msg_user,user.chat_id)
                newfeed_article = newfeed_article[10:]
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
    update_latesttime = list()
    for boardName in blt:
        if blt[boardName]['now_latest_time'] != blt[boardName]['pre_latest_time']:
            update_latesttime.append({'latest_time':blt[boardName]['now_latest_time'],'board':boardName})
    if len(to_update_pyptt_article) > 0:
        update_pyptt_article(to_update_pyptt_article)
    if len(update_latesttime) > 0:
        done = 0
        while done == 0:
            try:
                update_pyptt_board_latest_time(update_latesttime)
                done = 1
                logger.info('Update ptt newfeed successfully')
            except Exception as e:
                MessageService.tgNotifyMessage(f'{__name__} - Update PyPTT board list error:{e}')
                logger.error(str(e))
    logger.info('Checking for ptt newfeed successfully')
