import sqlalchemy
from .db_session import SqlAlchemyBase


class Player(SqlAlchemyBase):
    __tablename__ = 'players'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    role = sqlalchemy.Column(sqlalchemy.String)
    alive = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    voted = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    votes_num = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    chat_id = sqlalchemy.Column(sqlalchemy.String)