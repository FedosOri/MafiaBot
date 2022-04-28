from data.player import Player
from data.vars_for_mafia import Var
from data import db_session


def data_reset():
    db_sess = db_session.create_session()
    #  сброс списка игроков
    players = [player.name for player in get_all_players()]
    for player in players:
        db_sess.query(Player).filter(Player.name == player).delete()
        db_sess.commit()
    #  сброс значений
    db_sess.query(Var).filter(Var.name == "day_n").update({Var.var: "1"})
    db_sess.commit()

    var_list = ["start_game", "discussion", "mafia_time", "doctor_time",
                "commissar_time", "start_discussion", "vote_time", "night", "target"]
    for item in var_list:
        db_sess.query(Var).filter(Var.name == item).update({Var.var: ""})
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



