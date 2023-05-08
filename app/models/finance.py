from app.Extension import db

class FinanceUser(db.Model):
    __table__ = db.metadatas[None].tables['capital_user']

class CapitalFund(db.Model):
    __table__ = db.metadatas[None].tables['capital_fund_list']

class CapitalUserSubs(db.Model):
    __table__ = db.metadatas[None].tables['capital_user_subs']

class CathaybkEtf(db.Model):
    __table__ = db.metadatas[None].tables['cathaybk_etf_list']

class CathaybkEtfUserSubs(db.Model):
    __table__ = db.metadatas[None].tables['cathaybk_etf_user_subs']
