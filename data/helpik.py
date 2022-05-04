from data.player import Player
from data.vars_for_mafia import Var
from data.users import User
from data import db_session


def data_admin(k):
    if k == "all0":
        all0 = True
    else:
        all0 = False
    if k == "u1":
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        return users
    if k == "u0" or all0:
        db_sess = db_session.create_session()
        users = [u.name for u in db_sess.query(User).all()]
        for u in users:
            db_sess.query(User).filter(User.name == u).delete()
            db_sess.commit()
    if k == "p1":
        db_sess = db_session.create_session()
        players = db_sess.query(Player).all()
        return players
    if k == "p0" or all0:
        db_sess = db_session.create_session()
        players = [u.name for u in db_sess.query(Player).all()]
        for p in players:
            db_sess.query(User).filter(User.name == p).delete()
            db_sess.commit()
    if k == "v1":
        db_sess = db_session.create_session()
        vars = db_sess.query(Var).all()
        return vars
    if k == "v0" or all0:
        db_sess = db_session.create_session()
        vars = [u.name for u in db_sess.query(Var).all()]
        for v in vars:
            db_sess.query(Var).filter(Var.name == v).delete()
            db_sess.commit()


def data_reset():
    db_sess = db_session.create_session()
    #  сброс списка игроков
    players = [player.name for player in get_all_players()]
    for player in players:
        db_sess.query(Player).filter(Player.name == player).delete()
        db_sess.commit()
    #  сброс значений

    v = get_all_vars()
    if len(v) > 0:
        db_sess.query(Var).filter(Var.name == "day_n").update({Var.var: "1"})
        db_sess.commit()

        var_list = ["start_game", "discussion", "mafia_time", "doctor_time",
                    "commissar_time", "start_discussion", "vote_time", "night", "target"]
        for item in var_list:
            db_sess.query(Var).filter(Var.name == item).update({Var.var: ""})
            db_sess.commit()
    else:
        v = Var()
        v.name = "day_n"
        v.var = "1"
        db_sess.add(v)
        db_sess.commit()

        var_list = ["start_game", "discussion", "mafia_time", "doctor_time",
                    "commissar_time", "start_discussion", "vote_time", "night", "target"]
        for item in var_list:
            v = Var()
            v.name = item
            v.var = ""
            db_sess.add(v)
            db_sess.commit()


def set_default_var_for_players():
    db_sess = db_session.create_session()
    players = get_all_players()
    for player in players:
        db_sess.query(Player).filter(Player.name == player.name).update({Player.voted: False, Player.votes_num: 0})
        db_sess.commit()


def get_all_players():
    db_sess = db_session.create_session()
    players_list = db_sess.query(Player).all()
    return players_list


def get_all_vars():
    db_sess = db_session.create_session()
    var_list = db_sess.query(Var).all()
    return var_list


def save_all_vars(in_dict):
    db_sess = db_session.create_session()
    for item in in_dict:
        db_sess.query(Var).filter(Var.name == item).update({Var.var: in_dict[item]})
        db_sess.commit()



