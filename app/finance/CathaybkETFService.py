from flask import current_app
import requests
import datetime
import time
import json
import logging

from app.models.finance import FinanceUser, CathaybkEtf, CathaybkEtfUserSubs
from app import MessageService

config = current_app.config
db = current_app.extensions['sqlalchemy']

logger = logging.getLogger(__name__)

tzTaipei = datetime.timezone(datetime.timedelta(hours=+8))

def get_etf_with_user():
    all_results = (
        db.session
        .query(CathaybkEtf, FinanceUser)
        .filter(CathaybkEtfUserSubs.user_id == FinanceUser.id)
        .filter(CathaybkEtfUserSubs.etf_id == CathaybkEtf.etf_id)
        .distinct()
        .all()
        )
    return all_results

def crawl_cathaybk(etfId):
    todayStr = datetime.datetime.today().strftime("%Y-%m-%d")
    etf_info = {}
    try:
        url = f'https://cathaybk.moneydj.com/w/djjson/FundETFDataJSON.djjson?queryType=ROIChart&queryId={etfId}&datatype=ETF&rangeStart={todayStr}&rangeEnd={todayStr}'
        response = requests.get(url=url)
        dataRs = json.loads(response.content.decode('big5').encode('utf-8'))
        etf_info['name'] = dataRs['ResultSet']['data'][0]['return']['name']

        url = f'https://cathaybk.moneydj.com/w/djjson/FundETFDataJSON.djjson?queryType=ETFNavPriceCompare&queryId={etfId}'
        response = requests.get(url)
        dataRs = json.loads(response.content.decode('big5').encode('utf-8'))
        etf_info['detail'] = dataRs['ResultSet']['data'][1]
    except Exception as e:
        logger.error(str(e))
        return -1
    return etf_info


def update_cathaybk_etf_latest_day(eld_list):
    for etf, date in eld_list:
        etf.latest_day = date
    db.session.commit()
    return


def check_cathaybk_etf_newfeed():
    logger.info('Checking for cathaybk etf newfeed')
    today = datetime.datetime.now(tzTaipei).date()
    cathaybk_etf_list = get_etf_with_user()
    cel = { fund1[0]:[ fund2[1] for fund2 in cathaybk_etf_list if fund1[0]==fund2[0] ] for fund1 in cathaybk_etf_list}
    eld_list = []
    for etf, userList in cel.items():
        latest_date_in_db = etf.latest_day.astimezone(tzTaipei).date()
        if latest_date_in_db != today:
            try:
                cathaybkEtfInfo = crawl_cathaybk(etf.etf_id)
                latest_date_in_db_str = latest_date_in_db.strftime('%Y/%m/%d')
                etfName = cathaybkEtfInfo['name']
                latestday = cathaybkEtfInfo['detail']['date']
                netValue = cathaybkEtfInfo['detail']['p']
                netPercent = float(cathaybkEtfInfo['detail']['changeRFange'])
                if latestday != latest_date_in_db_str :
                    msg = f'{etfName}\n{latestday}\n淨值：{netValue}\n漲跌幅：{netPercent}%'
                    logger.info(msg)
                    eld_list.append((etf,datetime.datetime.strptime(latestday,'%Y/%m/%d').astimezone(tzTaipei)))
                    for user in userList:
                        MessageService.lineNotifyMessage(msg,user.chat_id)
            except Exception as e:
                MessageService.tgNotifyMessage(f'{__name__} - Error when crawl {etf.etf_id} - {e}')
                continue
    if len(eld_list) > 0 :
        done = 0
        while done == 0:
            try:
                update_cathaybk_etf_latest_day(eld_list)
                done = 1
                logger.info('Update cathaybk etf newfeed successfully')
            except Exception as e:
                MessageService.tgNotifyMessage(f'{__name__} - Update cathaybk etf list error:{e}')
                logger.error(str(e))
            time.sleep(1)
    logger.info('Checking for cathaybk etf newfeed successfully')
