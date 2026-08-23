from flask import render_template, request, Response
import logging

from app.store import bp, StoreService
from app import LogService

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('store/index.html')

@bp.route('/discord-bot-stock-subscribe')
def discord_bot_stock_subscribe():
    return render_template('store/discord_bot_subscribe.html')

@bp.route('/discord-bot-stock-subscribe/privacy')
def discord_bot_stock_subscribe_privacy():
    return render_template('store/discord_bot_privacy.html')

@bp.route('/discord-bot-stock-subscribe/terms')
def discord_bot_stock_subscribe_terms():
    return render_template('store/discord_bot_terms.html')

@bp.route('/ecpay/callback', methods = ['POST'])
def ecpay_callback():
    logger.debug(request.values)
    StoreService.callback_from_ecpay(request.values)
    return '1|OK'

@bp.route('/discord-bot-stock-subscribe/pay', methods = ['GET'])
def discord_bot_stock_subscribe_pay():
    subscription_type = request.args.get('type', None, type=str)
    return Response(StoreService.gen_ecpay_payment_page(subscription_type), mimetype='text/html')

@bp.route('/get-order-info', methods = ['GET'])
def get_order_info():
    order_id = request.args.get('order_id', None, type=str)
    ecparOrder = StoreService.get_order_info(order_id)
    return ecparOrder

@bp.route('/get-order-key', methods = ['GET'])
def get_order_key():
    order_id = request.args.get('order_id', None, type=str)
    discord_user_id = request.args.get('discord_user_id', None, type=str)
    code_list = StoreService.get_order_key(order_id, discord_user_id)
    return code_list

@bp.route('/redeem-key', methods = ['GET'])
def redeem_key():
    code = request.args.get('code', None, type=str)
    discord_user_id = request.args.get('discord_user_id', None, type=str)
    result = StoreService.redeem_key(code, discord_user_id)
    return result

@bp.after_request
def log_request(response):
    return LogService.log_request(response,logger)