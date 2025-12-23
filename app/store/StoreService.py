import logging
import datetime
import urllib
import hashlib
import uuid
import secrets
import hmac
import re
from zoneinfo import ZoneInfo

from flask import current_app

from app.models.store import EcpayOrder, DiscordBotRedeemCode

config = current_app.config

db = current_app.extensions['sqlalchemy']

logger = logging.getLogger(__name__)

tzTaipei = datetime.timezone(datetime.timedelta(hours=+8))

SECRET = bytes(config['DCBOT_CODE_SECRET'], encoding='utf-8')#

ALPHABET = config['DCBOT_CODE_ALPHABET']

def generate_hmac_key_20():
    # Step 1: 高隨機 nonce
    nonce = secrets.token_bytes(32)

    # Step 2: HMAC 簽名
    digest = hmac.new(SECRET, nonce, hashlib.sha256).digest()

    # Step 3: 將 digest 映射成可讀字元
    chars = []
    for b in digest:
        chars.append(ALPHABET[b % len(ALPHABET)])
        if len(chars) == 20:
            break

    # Step 4: 格式化
    key = "".join(chars)
    return "-".join([key[i:i+4] for i in range(0, 20, 4)])

KEY_REGEX = re.compile(r"^[A-Z2-9]{4}(-[A-Z2-9]{4}){4}$")

def is_valid_key_format(key: str) -> bool:
    return bool(KEY_REGEX.fullmatch(key))

def gen_ecpay_order(order_id, subscription_type, create_datetime, price, check_mac_value):
    ecpayOrder = EcpayOrder(order_id=order_id, subscription_type=subscription_type, price=price, ecpay_check_mac_value=check_mac_value, create_datetime=create_datetime)
    db.session.add(ecpayOrder)
    db.session.commit()
    return ecpayOrder

def get_check_mac_value_from_dict(dataform):
    sorted_dataform = dict(sorted(dataform.items()))
    sorted_dataform
    dataform_string = "&".join([f"{key}={value}" for key, value in sorted_dataform.items()])
    HashKey = config['ECPAY_HASH_KEY']
    HashIV = config['ECPAY_HASH_IV']
    dataform_string = f"HashKey={HashKey}&{dataform_string}&HashIV={HashIV}"
    dataform_string = urllib.parse.quote_plus(dataform_string)
    dataform_string = dataform_string.lower()
    dataform_string = hashlib.sha256(dataform_string.encode('utf-8')).hexdigest()
    dataform_string = dataform_string.upper()
    dataform_string
    return dataform_string

def gen_ecpay_payment_page(subscription_type):
    if subscription_type == 'one-members-one-year':
        price = config['ONE_MEMBERS_ONE_YEAR_PRICE']
        tradr_desc = '可無限使用機器人指令一年'
        item_name = '個人年度方案'
    elif subscription_type == 'four-members-one-year':
        price = config['FOUR_MEMBERS_ONE_YEAR_PRICE']
        tradr_desc = '更優惠的價格 可無限使用機器人指令一年'
        item_name = '家庭年度方案'
    url = config['ECPAY_CHECK_OUT_API']
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    order_id = "DCBOT" + datetime.datetime.now().astimezone(datetime.timezone.utc).astimezone(tzTaipei).strftime("%Y%m%d") + str(uuid.uuid4()).replace('-','')[:7].upper()
    create_datetime = datetime.datetime.now().astimezone(datetime.timezone.utc).astimezone(tzTaipei).strftime('%Y/%m/%d %H:%M:%S')
    dataform = {
        "MerchantID": config['ECPAY_MERCHANT_ID'],
        "MerchantTradeNo": order_id,
        "MerchantTradeDate": create_datetime,
        "PaymentType" :"aio",
        "TotalAmount" : price,
        "TradeDesc" : tradr_desc,
        "ItemName" : item_name,
        "ReturnURL" : config['ECPAY_RETURN_URL'],
        "ChoosePayment": "ALL",
        "EncryptType":1,
        "NeedExtraPaidInfo":"Y",
        
    }
    check_mac_value = get_check_mac_value_from_dict(dataform)
    dataform["CheckMacValue"] = check_mac_value
    ecpayOrder = gen_ecpay_order(order_id, subscription_type, create_datetime, price, check_mac_value)

    form_html = f"""
    <form id="ecpay-form" method="post" action="{url}">
        {''.join([f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in dataform.items()])}
    </form>
    <script>document.getElementById('ecpay-form').submit();</script>
    """

    return form_html

def callback_from_ecpay(request_data):
    order_id = request_data.get('MerchantTradeNo')
    ecpay_order_id = request_data.get('TradeNo')
    paid_datetime = request_data.get('PaymentDate')
    ecpay_payment_type = request_data.get('PaymentType')
    ecpay_rtn_msg = request_data.get('RtnMsg')
    ecpay_payment_type_charge_fee = request_data.get('PaymentTypeChargeFee')
    ecpay_rtn_code = request_data.get('RtnCode')
    ecpayOrder = EcpayOrder.query.filter(EcpayOrder.order_id == order_id).first()
    ecpayOrder.ecpay_order_id = ecpay_order_id
    ecpayOrder.paid_datetime = datetime.datetime.strptime(paid_datetime, '%Y/%m/%d %H:%M:%S').replace(tzinfo=ZoneInfo("Asia/Taipei"))
    ecpayOrder.ecpay_order_status = '1'
    ecpayOrder.ecpay_payment_type = ecpay_payment_type
    ecpayOrder.ecpay_rtn_msg = ecpay_rtn_msg
    ecpayOrder.ecpay_payment_type_charge_fee = ecpay_payment_type_charge_fee
    ecpayOrder.ecpay_rtn_code = ecpay_rtn_code
    db.session.commit()
    return

def get_order_info(order_id):
    ecpayOrder = EcpayOrder.query.filter(EcpayOrder.order_id == order_id).first()
    if not ecpayOrder:
        return {"message":"查無訂單"}
    return {
        "order_id": ecpayOrder.order_id,
        "ecpay_order_status": ecpayOrder.ecpay_order_status,
        "subscription_type": ecpayOrder.subscription_type,
        "discord_user_id": ecpayOrder.discord_user_id,
        "create_datetime": None if ecpayOrder.create_datetime == None else ecpayOrder.create_datetime.astimezone(tzTaipei).strftime('%Y-%m-%d %H:%M:%S'),
        "paid_datetime": None if ecpayOrder.paid_datetime == None else ecpayOrder.paid_datetime.astimezone(tzTaipei).strftime('%Y-%m-%d %H:%M:%S'),
        "redeem_datetime": None if ecpayOrder.redeem_datetime == None else ecpayOrder.redeem_datetime.astimezone(tzTaipei).strftime('%Y-%m-%d %H:%M:%S'),
        "price": ecpayOrder.price,
        "ecpay_payment_type": ecpayOrder.ecpay_payment_type,
        "ecpay_rtn_msg": ecpayOrder.ecpay_rtn_msg,
        "ecpay_payment_type_charge_fee": ecpayOrder.ecpay_payment_type_charge_fee,
        "ecpay_rtn_code": ecpayOrder.ecpay_rtn_code,
        "ecpay_check_mac_value": ecpayOrder.ecpay_check_mac_value,
    }

def get_order_key(order_id, discord_user_id):
    ecpayOrder = EcpayOrder.query.filter(EcpayOrder.order_id == order_id).first()
    if not ecpayOrder:
        return {"message":"查無訂單"}
    code_list = DiscordBotRedeemCode.query.filter(DiscordBotRedeemCode.order_id == order_id).all()
    if code_list:
        return [{
            "code": code_info.code,
            "status": code_info.status,
            "redeemed_datetime": None if code_info.redeemed_datetime == None else code_info.redeemed_datetime.astimezone(tzTaipei).strftime('%Y-%m-%d %H:%M:%S'),
            "redeemed_user_id": code_info.redeemed_user_id,
            "order_id": code_info.order_id,
            "create_datetime": None if code_info.create_datetime == None else code_info.create_datetime.astimezone(tzTaipei).strftime('%Y-%m-%d %H:%M:%S'),
                 } for code_info in code_list]
    now_datetime = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    if ecpayOrder.ecpay_rtn_code != '1':
        return {"message":"尚未繳費"}
    if ecpayOrder.subscription_type.startswith('one-members'):
        code_count = 1
    elif ecpayOrder.subscription_type.startswith('four-members'):
        code_count = 4
    if not ecpayOrder.ecpay_order_status:
        return {"message":"系統錯誤"}
    code_list = []
    for _ in range(code_count):
        key = generate_hmac_key_20()
        while DiscordBotRedeemCode.query.filter(DiscordBotRedeemCode.code == key).all():
            key = generate_hmac_key_20()
        discordBotRedeemCode = DiscordBotRedeemCode(code=key, order_id=order_id, status="0", create_datetime=now_datetime, redeemed_datetime=None, redeemed_user_id=None)
        code_list.append({
            "code": discordBotRedeemCode.code,
            "status": discordBotRedeemCode.status,
            "redeemed_datetime": discordBotRedeemCode.redeemed_datetime,
            "redeemed_user_id": discordBotRedeemCode.redeemed_user_id,
            "order_id": discordBotRedeemCode.order_id,
            "create_datetime": discordBotRedeemCode.create_datetime,
        })
        db.session.add(discordBotRedeemCode)
    ecpayOrder.ecpay_order_status = '2'
    ecpayOrder.redeem_datetime = now_datetime
    ecpayOrder.discord_user_id = discord_user_id
    db.session.commit()
    return code_list

def redeem_key(code, discord_user_id):
    discordBotRedeemCode = DiscordBotRedeemCode.query.filter(DiscordBotRedeemCode.code == code).first()
    if not discordBotRedeemCode:
        return {"message":"查無金鑰"}
    if discordBotRedeemCode.status == '1' and discordBotRedeemCode.redeemed_datetime and discordBotRedeemCode.redeemed_user_id:
        return {"message":"已被兌換"}
    if discordBotRedeemCode.status == '1' or discordBotRedeemCode.redeemed_datetime or discordBotRedeemCode.redeemed_user_id:
        return {"message":"系統錯誤"}
    if discordBotRedeemCode.status == '0' and not discordBotRedeemCode.redeemed_datetime and not discordBotRedeemCode.redeemed_user_id:
        discordBotRedeemCode.status = '1'
        discordBotRedeemCode.redeemed_datetime = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        discordBotRedeemCode.redeemed_user_id = discord_user_id
        ecpayOrder = EcpayOrder.query.filter(EcpayOrder.order_id == discordBotRedeemCode.order_id).first()
        subscription_type = ecpayOrder.subscription_type
        db.session.commit()
        return {"message":"兌換成功", "subscription_type":subscription_type}
    return {"message":"系統錯誤"}
