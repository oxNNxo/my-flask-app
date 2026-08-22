from app.Extension import db

class EcpayOrder(db.Model):
    __table__ = db.metadatas[None].tables['ecpay_order']
    __mapper_args__ = {
        'primary_key' : ['order_id']
    }

class DiscordBotRedeemCode(db.Model):
    __table__ = db.metadatas[None].tables['discord_bot_redeem_code']
    __mapper_args__ = {
        'primary_key' : ['code']
    }