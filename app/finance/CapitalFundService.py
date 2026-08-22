from flask import current_app
import requests
import datetime
import time
import json
import logging

from app.models.finance import FinanceUser, CapitalFund, CapitalUserSubs
from app import MessageService

config = current_app.config
db = current_app.extensions['sqlalchemy']

logger = logging.getLogger(__name__)

tzTaipei = datetime.timezone(datetime.timedelta(hours=+8))

def get_fund_with_user():
    all_results = (
        db.session
        .query(CapitalFund, FinanceUser)
        .filter(CapitalUserSubs.user_id == FinanceUser.id)
        .filter(CapitalUserSubs.fund_id == CapitalFund.fund_id)
        .distinct()
        .all()
        )
    return all_results


def crawl_capital(fundId):
    startday = (datetime.datetime.now()-datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    my_data = {"fundId":fundId,"start":startday,"end":today}
    try:
        capiresp = requests.get(url='https://www.capitalfund.com.tw/CFWeb/api/fund/detail/'+fundId)
    except Exception as e:
        logger.error(str(e))
        return -1
    return json.loads(capiresp.text)


def update_capital_fund_latest_day(fld_list):
    for fund, date in fld_list:
        fund.latest_day = date
    db.session.commit()
    return

def check_capitalfund_newfeed():
    logger.info('Checking for capital fund newfeed')
    today = datetime.datetime.now(tzTaipei).date()
    ful = get_fund_with_user()
    cfl = { fund1[0]:[ fund2[1] for fund2 in ful if fund1[0]==fund2[0] ] for fund1 in ful}
    fld_list = []
    for fund, userList in cfl.items():
        latest_date_in_db = fund.latest_day.astimezone(tzTaipei).date()
        if latest_date_in_db != today:
            try:
                capifund = crawl_capital(fund.fund_id)
                latest_date_in_db_str = latest_date_in_db.strftime('%Y-%m-%d')
                fundName = capifund['data']['fundName']
                fundShortname = capifund['data']['shortName']
                latestday = capifund['data']['netDate']
                netValue = capifund['data']['netValue']
                netPercent = capifund['data']['netPercent']
                if latestday[:10] != latest_date_in_db_str :
                    msg = f'{fundShortname}\n{latestday[:10]}\n淨值：{netValue}\n漲跌幅：{netPercent}%'
                    logger.info(msg)
                    fld_list.append((fund,datetime.datetime.strptime(latestday,'%Y-%m-%dT%H:%M:%S%z')))
                    for user in userList:
                        MessageService.lineNotifyMessage(msg,user.chat_id)
            except Exception as e:
                MessageService.tgNotifyMessage(f'{__name__} - Error when crawl {fund.fund_id} - {e}')
                continue
    if len(fld_list) > 0 :
        done = 0
        while done == 0:
            try:
                update_capital_fund_latest_day(fld_list)
                done = 1
                logger.info('Update capital fund newfeed successfully')
            except Exception as e:
                MessageService.tgNotifyMessage(f'{__name__} - Update capital fund list error:{e}')
                logger.error(str(e))
        time.sleep(1)
    logger.info('Checking for capital fund newfeed successfully')
