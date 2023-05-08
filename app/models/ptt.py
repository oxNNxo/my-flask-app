from app.Extension import db

class User(db.Model):
    __table__ = db.metadatas[None].tables['pyptt_user']

class Board(db.Model):
    __table__ = db.metadatas[None].tables['pyptt_board_list']

class Article(db.Model):
    __table__ = db.metadatas[None].tables['pyptt_article']
    __mapper_args__ = {
        'primary_key' : ['published', 'board', 'author']
    }

class Subs(db.Model):
    __table__ = db.metadatas[None].tables['pyptt_subs']

class UserSubs(db.Model):
    __table__ = db.metadatas[None].tables['pyptt_user_subs']
    __mapper_args__ = {
        'primary_key' : ['user_id', 'subs_id']
    }
