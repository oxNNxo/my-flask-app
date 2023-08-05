from flask import current_app
import logging

from app.finance import CapitalFundService
from app.finance import CathaybkETFService
from app.ptt import PttService
from app import CommonService

config = current_app.config
scheduler = current_app.apscheduler

logger = logging.getLogger(__name__)

@scheduler.task(id='check_ptt_newfeed_and_delete_old_articles', trigger='interval', minutes=config['PTT_CRAWLER_PERIOD'], misfire_grace_time=30,)
def schedulerJobs_check_ptt_newfeed():
    with scheduler.app.app_context():
        PttService.check_ptt_newfeed()
        PttService.delete_old_articles(days = 7)


@scheduler.task(id='check_capitalfund_newfeed', trigger='interval', minutes=config['CAPITAL_FUND_CRAWLER_PERIOD'], misfire_grace_time=30,)
def schedulerJobs_check_capitalfund_newfeed():
    with scheduler.app.app_context():
        CapitalFundService.check_capitalfund_newfeed()


@scheduler.task(id='check_cathaybk_etf_newfeed', trigger='interval', minutes=config['CATHAY_ETF_CRAWLER_PERIOD'], misfire_grace_time=30,)
def schedulerJobs_check_cathaybk_etf_newfeed():
    with scheduler.app.app_context():
        CathaybkETFService.check_cathaybk_etf_newfeed()


@scheduler.task(id='wake_up_myself', trigger='interval', minutes=config['WAKE_UP_MYSELF_PERIOD'], misfire_grace_time=30,)
def schedulerJobs_wake_up_myself():
    with scheduler.app.app_context():
        CommonService.wake_up_myself()