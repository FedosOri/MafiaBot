import sqlalchemy
from .db_session import SqlAlchemyBase


class Var(SqlAlchemyBase):
    __tablename__ = 'vars'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    var = sqlalchemy.Column(sqlalchemy.String)
