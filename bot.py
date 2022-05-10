import telebot
from telebot import types
import csv
import random
from data.player import Player
from data.users import User
from data.vars_for_mafia import Var
from data import helpik, config, db_session


db_session.global_init("db/theplaybot.db")
bot = telebot.TeleBot(config.token)

log = False
game = ''
last_sms = ''
checkpoint = 0
town_list = []

f = open('static/russian_nouns.txt', 'r', encoding='utf-8')
all_words = f.readlines()

earnings = 0
flag = 0
situation = ''

hidden_word = ''
inferred_word = ''
mistakes = 0
letter_list = []
user_number = 0


@bot.message_handler(commands=['start'])
def welcome(message):
    global game, last_sms, checkpoint, town_list, hidden_word, \
        earnings, inferred_word, mistakes, letter_list, user_number

    game = ''
    last_sms = ''
    checkpoint = 0
    town_list = []
    hidden_word = ''
    inferred_word = ''
    earnings = 0
    mistakes = 0
    letter_list = []
    user_number = 0

    sti = open('data/Hello.webp', 'rb')
    user_id = str(message.from_user.username)
    bot.send_sticker(message.chat.id, sti)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("📄 Регистрация")
    item2 = types.KeyboardButton("🦔 Вход")
    item3 = types.KeyboardButton("🔫 Мафия")

    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, "Если Вы не зарегистрировались, можете это сделать. Либо войдите в свой аккаунт"
                                      .format(message.from_user, bot.get_me()), reply_markup=markup)

    # helpik.data_reset()


@bot.message_handler(commands=['balance'])
def goodbye(message):
    global earnings, user_number
    sti = open('data/thanks.tgs', 'rb')
    user_id = str(message.from_user.username)
    bot.send_sticker(message.chat.id, sti)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_number).first()

    user.balance += earnings
    db_sess.commit()
    bot.send_message(message.chat.id, "Баланс пополнен. Заходите еще")
    earnings = 0


@bot.message_handler(commands=["info"])
def description(message):
    file = open('data/description.txt', 'r', encoding='utf-8')
    mes = file.readlines()
    bot.send_message(message.chat.id, "".join(mes), parse_mode="Markdown")


@bot.message_handler(commands=["data"])
def for_admin(message):
    mes = message.text.split()
    if len(mes) > 1 and message.from_user.username in config.super_admins:
        if mes[1] == "all0":
            helpik.data_admin("all0")
            mes = "готово"
        elif mes[1] == "u1":
            users = [u.name for u in helpik.data_admin("u1")]
            mes = "пользователи:\n"
            for u in users:
                mes += u + "\n"
        elif mes[1] == "u0":
            helpik.data_admin("u0")
            mes = "готово"
        elif mes[1] == "p1":
            players = [p.name for p in helpik.data_admin("p1")]
            mes = "игроки:\n"
            for p in players:
                mes += p + "\n"
        elif mes[1] == "p0":
            helpik.data_admin("p0")
            mes = "готово"
        elif mes[1] == "v1":
            vars = [v.name for v in helpik.data_admin("v1")]
            mes = "значения:\n"
            for v in vars:
                mes += v + "\n"
        elif mes[1] == "v0":
            helpik.data_admin("v0")
            mes = "готово"
        elif mes[1] == "pv0":
            helpik.data_reset()
            mes = "готово"
        else:
            mes = "all0 - сбросить все\n" \
                  "\n" \
                  "u1 - вывести всех пользователей\n" \
                  "u0 - сбросить пользователей\n" \
                  "\n" \
                  "p1 - вывести всех игроков\n" \
                  "p0 - сбросить игроков\n" \
                  "\n" \
                  "v1 - вывести все значения\n" \
                  "v0 - сбросить значения\n"
        bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["players"])
def alive_players(message):
    var_dict = {}
    for item in helpik.get_all_vars():
        var_dict[item.name] = item.var
    if var_dict["start_game"]:
        players = helpik.get_all_players()
        players_alive = "Живые игроки:"
        players_not_alive = "Не живые игроки:"
        for player in players:
            if player.alive:
                players_alive += "\n @" + player.name
            else:
                players_not_alive += "\n @" + player.name
        bot.send_message(message.chat.id, players_alive)
        bot.send_message(message.chat.id, players_not_alive)
    else:
        mes = "Игра не начата."
        bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["join"])
def join(message):
    var_dict = {}
    for item in helpik.get_all_vars():
        var_dict[item.name] = item.var
    if not var_dict["start_game"]:
        name_for_add = message.from_user.username
        players = [player.name for player in helpik.get_all_players()]
        print(players)
        if name_for_add not in players:
            db_sess = db_session.create_session()
            player = Player()
            if name_for_add is None:
                mes = f"Чтобы присоединиться, создайте имя пользователя в настройках тг."
                bot.send_message(message.chat.id, mes)
            player.name = name_for_add
            player.chat_id = message.chat.id
            db_sess.add(player)
            db_sess.commit()

            mes = f"Вы добавлены.\nВот ссылка на комнату {config.channel}, если вас там еще нет."
            bot.send_message(message.chat.id, mes)

            if check_admin(message.from_user.username):
                mes = f"Игрок @{name_for_add}(админ) присоединился к игре."
                bot.send_message(config.channel, mes)
            else:
                mes = f"Игрок @{name_for_add} присоединился к игре."
                bot.send_message(config.channel, mes)
        else:
            mes = f"Мне кажется, что вы уже присоединились."
            bot.send_message(message.chat.id, mes)
    else:
        mes = "Игра запущена!"
        bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["start_game"])
def game(message):
    if check_admin(message.from_user.username):
        var_dict = {}
        for item in helpik.get_all_vars():
            var_dict[item.name] = item.var
        if not var_dict["start_game"]:
            players = helpik.get_all_players()

            mafia = []
            doctor = []
            commissar = []
            peaceful = []
            players_n = len(players)

            if players_n <= 2:
                mes = "Игроков слишком мало для начала игры!"
                bot.send_message(config.channel, mes)
            else:
                random.shuffle(players)
                doctor.append(players[0])
                commissar.append(players[1])
                if players_n <= 5:
                    mafia.append(players[2])
                    for player in players[3:]:
                        peaceful.append(player)
                elif players_n <= 10:
                    mafia.append(players[2])
                    mafia.append(players[3])
                    for player in players[4:]:
                        peaceful.append(player)
                else:
                    mafia.append(players[2])
                    mafia.append(players[3])
                    mafia.append(players[5])
                    for player in players[6:]:
                        peaceful.append(player)

                info_mafia = ["@" + player.name for player in mafia]
                for player in mafia:
                    mes = "Мафии на эту игру:"
                    for item in info_mafia:
                        mes += "\n" + item
                    bot.send_message(player.chat_id, mes)
                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == player.name).update({Player.role: "mafia"})
                    db_sess.commit()

                for player in doctor:
                    mes = "Вы доктор!"
                    bot.send_message(player.chat_id, mes)
                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == player.name).update({Player.role: "doctor"})
                    db_sess.commit()

                for player in commissar:
                    mes = "Вы комиссар!"
                    bot.send_message(player.chat_id, mes)
                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == player.name).update({Player.role: "commissar"})
                    db_sess.commit()

                for player in peaceful:
                    mes = "Вы мирный житель!"
                    bot.send_message(player.chat_id, mes)
                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == player.name).update({Player.role: "peaceful"})
                    db_sess.commit()

                # # инфо код
                # mes = ""
                # for player in helpik.get_all_players():
                #     mes += "\n@" + player.name + " " + player.role
                # bot.send_message(config.channel, mes)

                mes = "Игроки:"
                random.shuffle(players)
                for player in players:
                    mes += "\n@" + player.name
                bot.send_message(config.channel, mes)

                bot.send_message(config.channel, f"День {var_dict['day_n']}")

                mes = "Добро пожаловать в игру!\n" \
                      "Все получили свои роли!\n" \
                      "Итак, давайте знакомится!\n" \
                      "Когда будете готовы, отправьте\n/stop_discussion."
                bot.send_message(config.channel, mes)

                var_dict["start_game"] = "True"
                var_dict["discussion"] = "True"
                helpik.save_all_vars(var_dict)
        else:
            bot.send_message(message.chat.id, "Игра уже запущена!")
    else:
        mes = "У вас нет доступа к команде /start_game!"
        bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=["stop_game"])
def stop_game(message):
    if check_admin(message.from_user.username):
        var_dict = {}
        for item in helpik.get_all_vars():
            var_dict[item.name] = item.var

        if var_dict["start_game"]:
            mes = "Игрок @" + message.from_user.username + " решил завершить игру!"
            bot.send_message(config.channel, mes)
            #  сброс всех данных
            helpik.data_reset()
        else:
            mes = "Игра не начата."
            bot.send_message(message.chat.id, mes)
    else:
        mes = "У вас нет доступа к команде /stop_game!"
        bot.send_message(message.chat.id, mes)


@bot.message_handler(commands=['stop_discussion'])
def game_process(message):
    players = [player.name for player in helpik.get_all_players()]
    if message.from_user.username in players:
        if check_admin(message.from_user.username):
            var_dict = {}
            for item in helpik.get_all_vars():
                var_dict[item.name] = item.var
            if var_dict["start_game"]:
                if not var_dict["night"]:
                    if var_dict["day_n"] != "1":
                        mes = "Пришло время выбирать, кого будем казнить!\n" \
                              "Отправьте ваш выбор, я все подсчитаю и вынесу вердикт."
                        bot.send_message(config.channel, mes)

                        var_dict["discussion"] = ""
                        var_dict["vote_time"] = "True"

                        players = helpik.get_all_players()
                        mes = "Живые игроки:"
                        for player in players:
                            if player.alive:
                                mes += "\n @" + player.name
                        bot.send_message(config.channel, mes)

                        helpik.save_all_vars(var_dict)
                    else:
                        mes = "Наступает ночь, город засыпает, да прольется кровь!"
                        bot.send_message(config.channel, mes)

                        players = helpik.get_all_players()
                        alive_mafia = []
                        for m in players:
                            if m.role == "mafia" and m.alive:
                                alive_mafia.append(m)

                        if len(alive_mafia) > 1:
                            mes += "Так как мафий больше 1, то я случайно выберу ту, кто будет УБИВАТЬ!"
                            bot.send_message(config.channel, mes)
                            super_mafia = random.choice(alive_mafia)
                            mes = "Вы должны сделать выбор!"
                            bot.send_message(super_mafia.chat_id, mes)
                        else:
                            mes = "Мафия, напишите мне в личные сообщения вашу цель."
                            bot.send_message(config.channel, mes)

                        var_dict["mafia_time"] = "True"
                        var_dict["discussion"] = ""
                        var_dict["night"] = "True"
                        var_dict["vote_time"] = ""

                        helpik.save_all_vars(var_dict)
                else:
                    mes = "Сейчас нельзя использовать эту команду."
                    bot.send_message(message.chat.id, mes)
            else:
                mes = "Игра не начата."
                bot.send_message(message.chat.id, mes)
        else:
            mes = "У вас нет доступа к команде /stop_discussion!"
            bot.send_message(message.chat.id, mes)
    else:
        mes = "Вы не участвуете в игре, не мешайте процессу!"
        bot.send_message(config.channel, mes)


@bot.message_handler(content_types=['text'])
def communication(message):
    if message.chat.type == 'private':
        global game, last_sms, checkpoint, town_list, all_words, \
            earnings, hidden_word, inferred_word, mistakes, letter_list, flag, situation, user_number
        if message.text == "🔫 Мафия":
            welcome_mes = "Доброе утро, это игра мафия." \
                          "\nКоманды для админов:" \
                          "\n/start_game" \
                          "\n/stop_game" \
                          "\n/stop_discussion" \
                          "\nКоманды для всех:" \
                          "\n/join" \
                          "\n/players" \
                          "\n/info"
            bot.send_message(message.chat.id, welcome_mes)
            situation = "mafia"

        elif message.text == "📄 Регистрация":
            bot.send_message(message.chat.id, "Чтобы зарегистрироваться, введите пароль.")
            situation = "registration"

        elif situation == "registration":
            db_sess = db_session.create_session()

            user = User()
            user.name = message.from_user.username
            user.hashed_password = message.text
            fl = True
            for user in db_sess.query(User).filter(User.name == user.name):
                fl = False
            if fl and message.text != "🦔 Вход" and message.text != "📄 Регистрация":
                db_sess.add(user)
                db_sess.commit()
                situation = "entry"
                bot.send_message(message.chat.id, "Регистрация прошла успешно, теперь войдите в аккаунт")
            else:
                if message.text != "🦔 Вход" and message.text != "📄 Регистрация":
                    bot.send_message(message.chat.id, "Этот пользователь уже зарегистрирован")
                else:
                    if message.text == "🦔 Вход":
                        bot.send_message(message.chat.id, "Чтобы войти, введите пароль.")
                        situation = 'entry'

                    elif message.text == "📄 Регистрация":
                        bot.send_message(message.chat.id, "Чтобы зарегистрироваться, введите пароль.")
                        situation = 'entry'

        elif message.text == "🦔 Вход":
            bot.send_message(message.chat.id, "Чтобы войти, введите пароль.")
            situation = "entry"

        elif situation == "entry":

            db_sess = db_session.create_session()
            user = User()
            user.name = message.from_user.username
            user.hashed_password = message.text
            result = False
            for user in db_sess.query(User).filter(User.name == user.name,
                                                   User.hashed_password == user.hashed_password):
                user_number = user.id
                result = True
            if result and message.text != "🦔 Вход" and message.text != "📄 Регистрация":
                bot.send_message(message.chat.id, "Вы вошли")
                situation = 'login completed'

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("🏙 Города")
                item2 = types.KeyboardButton("🪙 Бросить монетку")
                item3 = types.KeyboardButton("웃 Виселица")
                item4 = types.KeyboardButton("❓ Число")
                item5 = types.KeyboardButton("🏆 Лидеры")
                item6 = types.KeyboardButton("💰 Выигрыш сегодня")
                item7 = types.KeyboardButton("🔫 Мафия")
                item8 = types.KeyboardButton("/start")
                item9 = types.KeyboardButton("/balance")

                markup.add(item1, item2, item3, item4, item5, item6, item7, item8, item9)

                bot.send_message(message.chat.id, "Ещё раз здравствуй, \nЯ - <b>Бот, который может многое.</b>"
                                                  " Я могу поиграть в города, бросить монетку, назвать случайное число"
                                                  " и сыграть в висилицу.\n /balance - Пополняет баланс. И записывает"
                                                  " в базу обновленный счет. Не забывайте использовать эту команду. "
                                                  "Иначе прогресс НЕ СОХРАНИТСЯ \n /start - Начинает работу бота"
                                                  " и также служит как выход из аккаунта."
                                 .format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)

            else:
                if message.text != "🦔 Вход" and message.text != "📄 Регистрация":
                    bot.send_message(message.chat.id, "Неверный пароль")
                else:
                    if message.text == "🦔 Вход":
                        situation = 'entry'
                        bot.send_message(message.chat.id, "Чтобы войти, введите пароль.")
                    if message.text == "📄 Регистрация":
                        situation = 'registration'
                        bot.send_message(message.chat.id, "Чтобы зарегистрироваться, введите пароль.")

        elif situation == 'login completed':
            if message.text == '🏙 Города' and game == '':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Я")
                item2 = types.KeyboardButton("Ты")

                markup.add(item1, item2)
                game = 'towns'
                bot.send_message(message.chat.id, "Ну давай начнем. Кто первый?"
                                 .format(message.from_user, bot.get_me()), reply_markup=markup)

            elif message.text == '🪙 Бросить монетку' and game == '':
                sti = open('data/coin.tgs', 'rb')
                coins = ["Орёл", "Решка"]
                a = random.randint(0, 1)
                b = random.randint(0, 1)
                bot.send_message(message.chat.id, f"Мне кажется выпадет {coins[b]}")
                bot.send_sticker(message.chat.id, sti)

                if coins[a] == 'Решка':
                    if a == b:
                        bot.send_message(message.chat.id, f"Монетка упала. Выпала {coins[a]}. Ура, я угадал 😃")
                        earnings += 5
                    else:
                        bot.send_message(message.chat.id, f"Монетка упала. Выпала {coins[a]}. Я не угадал 😞")
                        earnings += 3
                elif coins[a] == 'Орёл':
                    if a == b:
                        bot.send_message(message.chat.id, f"Монетка упала. Выпал {coins[a]}. Ура, я угадал 😃")
                        earnings += 5
                    else:
                        bot.send_message(message.chat.id, f"Монетка упала. Выпал {coins[a]}. Я не угадал 😞")
                        earnings += 3

            elif message.text == '❓ Число' and game == '':
                earnings += 2
                a = random.randint(1, 100)
                bot.send_message(message.chat.id, f"Случайным образом выпало число - {a}")

            elif message.text == '웃 Виселица' and game == '':
                a = random.randint(0, len(all_words) - 1)
                hidden_word = all_words[a].rstrip()

                while len(hidden_word) < 5:
                    a = random.randint(0, len(all_words) - 1)
                    hidden_word = all_words[a].rstrip()

                inferred_word = '_ ' * len(hidden_word)
                print(inferred_word)
                game = 'gallows'

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("🚪 Выйти")
                markup.add(item1)
                mess = f"Я загадал слово {inferred_word}"
                bot.send_message(message.chat.id, mess
                                 .format(message.from_user, bot.get_me()),
                                 reply_markup=markup)

            elif message.text == '🏆 Лидеры':
                db_sess = db_session.create_session()
                leaders = {}
                for user in db_sess.query(User).all():
                    leaders[user.name] = user.balance
                leaders = sorted(leaders.items(), key=lambda x: x[1])
                leaders.reverse()
                output = ''
                for i in range(len(leaders)):
                    if i < 3:
                        output += f'{i + 1}. {leaders[i][0]} - {leaders[i][1]}\n'
                bot.send_message(message.chat.id, f"{output}")

            elif message.text == '💰 Выигрыш сегодня':
                bot.send_message(message.chat.id, f"{earnings}")

            elif message.text == 'Я' and game == "towns" and checkpoint == 0:
                checkpoint = 1
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("🚪 Выйти")
                item2 = types.KeyboardButton("Показать уже названные города")
                markup.add(item1, item2)
                bot.send_message(message.chat.id, "Начинай".format(message.from_user, bot.get_me()),
                                 reply_markup=markup)
                checkpoint = 1

            elif message.text == 'Ты' and game == "towns" and checkpoint == 0:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("🚪 Выйти")
                item2 = types.KeyboardButton("Показать уже названные города")
                markup.add(item1, item2)
                bot.send_message(message.chat.id, "Москва, твой ход".format(message.from_user, bot.get_me()),
                                 reply_markup=markup)
                checkpoint = 1
                last_sms = 'Москва'
                town_list.append(last_sms)

            elif message.text == '🚪 Выйти':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("🏙 Города")
                item2 = types.KeyboardButton("🪙 Бросить монетку")
                item3 = types.KeyboardButton("웃 Виселица")
                item4 = types.KeyboardButton("❓ Число")
                item5 = types.KeyboardButton("🏆 Лидеры")
                item6 = types.KeyboardButton("💰 Выигрыш сегодня")
                item7 = types.KeyboardButton("🔫 Мафия")
                item8 = types.KeyboardButton("/start")
                item9 = types.KeyboardButton("/balance")

                markup.add(item1, item2, item3, item4, item5, item6, item7, item8, item9)

                bot.send_message(message.chat.id, "Молодец, хорошо сыграли. Приходи ещё!"
                                 .format(message.from_user, bot.get_me()), reply_markup=markup)
                game = ''
                last_sms = ''
                checkpoint = 0
                town_list = []

            elif message.text == 'Показать уже названные города' and game == "towns" and checkpoint == 1:
                sp = ', '.join(town_list)
                if len(sp) > 0:
                    bot.send_message(message.chat.id, f"{sp}")
                else:
                    bot.send_message(message.chat.id, "Пока что их там нет")

            else:
                # ГОРОДА
                if game == 'towns' and checkpoint == 1:
                    nach = message.text[0]
                    kon = message.text[-1]

                    b = -1
                    while kon in ['ь', 'ъ', 'ы']:
                        kon = message.text[b]
                        b -= 1

                    if last_sms != '':
                        a = last_sms[-1].upper()
                        b = -1

                        while a in ['Ь', 'Ъ', 'Ы']:
                            a = last_sms[b - 1].upper()
                            b -= 1
                        if nach == a:
                            with open('static/goroda.csv') as csvfile:
                                file_reader = csv.reader(csvfile, delimiter=";")
                                fl = 0
                                for i in file_reader:
                                    word = i[6]
                                    if word == message.text:
                                        fl = 1
                                        break
                                if fl == 1 and message.text not in town_list:
                                    earnings += 150
                                    for i in file_reader:
                                        word = i[6]
                                        if word[0] == kon.upper() and word not in town_list:
                                            bot.send_message(message.chat.id, f"{word}"
                                                                              f"\nСтрана: {i[4]}"
                                                                              f"\nЧисленность: {i[-1]} чел."
                                                                              f"\nКоординаты: {i[7]}, {i[8]}")

                                            break
                                    last_sms = f'{word}'
                                    town_list.append(message.text)
                                    town_list.append(last_sms)
                                else:
                                    if message.text in town_list:
                                        bot.send_message(message.chat.id, "Уже было")
                                    else:
                                        bot.send_message(message.chat.id, "Такого города не существует")

                        else:
                            bot.send_message(message.chat.id, "Слово у тебя не с той буквы начинается")

                    else:
                        last_sms = message.text
                        earnings += 150
                        a = last_sms[-1].upper()
                        b = -1

                        while a in ['Ь', 'Ъ', 'Ы']:
                            a = last_sms[b - 1].upper()
                            b -= 1
                        with open('static/goroda.csv') as csvfile:
                            file_reader = csv.reader(csvfile, delimiter=";")
                            fl = 0
                            for i in file_reader:
                                slovo = i[6]

                                if slovo == message.text:
                                    fl = 1
                                    break
                            if fl == 1 and last_sms not in town_list:
                                for i in file_reader:
                                    slovo = i[6]
                                    if slovo[0] == a:
                                        bot.send_message(message.chat.id, f"{slovo}"
                                                                          f"\nСтрана: {i[4]}"
                                                                          f"\nЧисленность: {i[-1]} чел."
                                                                          f"\nКоординаты: {i[7]}, {i[8]}")
                                        break
                                town_list.append(last_sms)
                                town_list.append(slovo)
                                last_sms = f'{slovo}'
                            else:
                                if last_sms in town_list:
                                    last_sms = ''
                                    bot.send_message(message.chat.id, "Уже было")
                                else:
                                    last_sms = ''
                                    bot.send_message(message.chat.id, "Такого города не существует")
                # ГОРОДА

                # ВИСИЛИЦА
                elif game == 'gallows':
                    print(hidden_word)
                    if len(message.text) == 1:
                        if message.text.lower() in hidden_word:
                            if message.text.lower() in letter_list:
                                bot.send_message(message.chat.id, "Уже была такая буква")
                            else:
                                sp = hidden_word
                                new_inferred_word = ''
                                for i in sp:
                                    if i == message.text.lower():
                                        new_inferred_word += message.text.lower()
                                        new_inferred_word += ' '
                                    else:
                                        new_inferred_word += '_ '
                                inferred_word = inferred_word.split(' ')
                                new_inferred_word = new_inferred_word.split(' ')
                                for i in range(len(inferred_word)):
                                    if inferred_word[i] == '_' and new_inferred_word[i] != '_':
                                        inferred_word[i] = new_inferred_word[i]
                                inferred_word = ' '.join(inferred_word)
                                bot.send_message(message.chat.id, f"{inferred_word}")
                                letter_list.append(message.text.lower())
                                if '_' not in inferred_word:
                                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                    item1 = types.KeyboardButton("🚪 Выйти")

                                    markup.add(item1)
                                    bot.send_message(message.chat.id,
                                                     "Поздравляю, Вы выиграли. За игру Вы получаете 3000 очков"
                                                     .format(message.from_user, bot.get_me()), reply_markup=markup)

                                    earnings += 3000
                                    game = ''
                                    hidden_word = ''
                                    inferred_word = ''
                                    mistakes = 0
                                    letter_list = []
                        else:
                            if message.text.lower() in letter_list:
                                bot.send_message(message.chat.id, "Уже была такая буква")
                            else:
                                mistakes += 1
                                img = open(f'data/{mistakes}.png', 'rb')
                                bot.send_photo(message.chat.id, img)
                                bot.send_message(message.chat.id, f"{inferred_word}")
                                letter_list.append(message.text.lower())
                                if mistakes == 10:
                                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                    item1 = types.KeyboardButton("🚪 Выйти")

                                    markup.add(item1)
                                    bot.send_message(message.chat.id,
                                                     "К сожалению, Вы проиграли. За игру Вы получаете -100 очков"
                                                     .format(message.from_user, bot.get_me()), reply_markup=markup)

                                    earnings += -100
                                    game = ''
                                    hidden_word = ''
                                    inferred_word = ''
                                    mistakes = 0
                                    letter_list = []
                    else:
                        if message.text.lower() == hidden_word:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                            item1 = types.KeyboardButton("🚪 Выйти")

                            markup.add(item1)
                            bot.send_message(message.chat.id,
                                             "Поздравляю, Вы выиграли. За игру Вы получаете 3000 очков"
                                             .format(message.from_user, bot.get_me()), reply_markup=markup)

                            earnings += 3000
                            game = ''
                            hidden_word = ''
                            inferred_word = ''
                            mistakes = 0
                            letter_list = []
                        else:
                            mistakes += 1
                            img = open(f'data/{mistakes}.png', 'rb')
                            bot.send_photo(message.chat.id, img)
                            if mistakes == 10:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                item1 = types.KeyboardButton("🚪 Выйти")

                                markup.add(item1)
                                bot.send_message(message.chat.id,
                                                 "К сожалению, Вы проиграли. За игру Вы получаете -100 очков"
                                                 .format(message.from_user, bot.get_me()), reply_markup=markup)

                                earnings += -100
                                game = ''
                                hidden_word = ''
                                inferred_word = ''
                                mistakes = 0
                                letter_list = []
                # ВИСИЛИЦА

                # ОШИБКА
                else:
                    bot.send_message(message.chat.id, "Не понимаю о чем Вы, друг мой.")
                # ОШИБКА

    var_dict = {}
    for item in helpik.get_all_vars():
        var_dict[item.name] = item.var

    if var_dict["start_game"]:
        players = [player.name for player in helpik.get_all_players()]
        if message.from_user.username in players:
            if var_dict["vote_time"]:
                who_voted = message.from_user.username
                against_who = message.text
                db_sess = db_session.create_session()
                player_who_voted = db_sess.query(Player).filter(Player.name == who_voted).first()
                player_against_who = db_sess.query(Player).filter(Player.name == against_who).first()
                players = [player.name for player in helpik.get_all_players()]

                if who_voted == against_who:
                    mes = "Против себя нельзя голосовать!"
                    bot.send_message(message.chat.id, mes)
                elif player_who_voted.voted:
                    mes = "Вы уже проголосовали!"
                    bot.send_message(message.chat.id, mes)
                elif against_who not in players:
                    mes = "Такого игрока нет!"
                    bot.send_message(message.chat.id, mes)
                elif not player_against_who.alive:
                    mes = f"Против @{against_who} голосовать, потому что он мертв!"
                    bot.send_message(message.chat.id, mes)
                else:
                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == who_voted).update({Player.voted: True})
                    db_sess.commit()
                    db_sess.query(Player).filter(Player.name == against_who).\
                        update({Player.votes_num: Player.votes_num + 1})
                    db_sess.commit()

                stop_vote = True

                for player in helpik.get_all_players():
                    if not player.voted and player.alive:
                        stop_vote = False
                        break

                if stop_vote:
                    mes = "Все проголосовали."
                    bot.send_message(config.channel, mes, reply_markup=types.ReplyKeyboardRemove())

                    most_votes = 0
                    who_will_be_killed = ""
                    for player in helpik.get_all_players():
                        if player.votes_num >= most_votes:
                            most_votes = player.votes_num
                            who_will_be_killed = player.name

                    helpik.set_default_var_for_players()

                    db_sess = db_session.create_session()
                    db_sess.query(Player).filter(Player.name == who_will_be_killed).update({Player.alive: False})
                    db_sess.commit()
                    player = db_sess.query(Player).filter(Player.name == who_will_be_killed).first()

                    mes = "Итак, вы решили уничтожить @" + who_will_be_killed + "."
                    if player.role == "mafia":
                        mes += "\nВы сделали правильный выбор! Это мафия!."
                    elif player.role == "doctor":
                        mes += "\nКак вы могли... Это был ваш доктор."
                    elif player.role == "commissar":
                        mes += "\nЧто вы наделали... Это был комиссар."
                    else:
                        mes += "\nВы совершили ошибку... Это был мирный житель..."
                    bot.send_message(config.channel, mes)

                    mafia = []
                    mafia_n = 0
                    not_mafia_n = 0
                    players = helpik.get_all_players()
                    for m in players:
                        if m.alive:
                            if m.role == "mafia":
                                mafia_n += 1
                                mafia.append(m)
                            else:
                                not_mafia_n += 1

                    if mafia_n == 0:
                        victory("peaceful")
                        return
                    elif not_mafia_n <= 0:
                        victory("mafia")
                        return

                    mes = "Наступает ночь, город засыпает, да прольется кровь!"
                    bot.send_message(config.channel, mes)

                    if mafia_n > 1:
                        mes = "Так как мафий больше 1, то я случайно выберу ту, кто будет УБИВАТЬ!"
                        for m in mafia:
                            bot.send_message(m.chat_id, mes)

                        super_mafia = random.choice(mafia)
                        mes = "Вы должны сделать выбор!"
                        bot.send_message(super_mafia.chat_id, mes)
                    else:
                        mafia = db_sess.query(Player).filter(Player.role == "mafia", Player.alive is True).first()
                        mes = "Мафия просыпается. Мафия, напишите мне в личные сообщения вашу цель."
                        bot.send_message(config.channel, mes)

                    var_dict["mafia_time"] = "True"
                    var_dict["vote_time"] = ""
                    var_dict["night"] = "True"
                    helpik.save_all_vars(var_dict)

            elif var_dict["night"]:
                db_sess = db_session.create_session()
                player = db_sess.query(Player).filter(Player.name == message.from_user.username).first()

                if not player.alive:
                    bot.delete_message(message.chat.id, message.message_id)
                    mes = "Увы, мертвые не говорят..."
                    bot.send_message(message.chat.id, mes)

                if var_dict["mafia_time"] and player.role == "mafia":
                    players = {player.name: player.alive for player in helpik.get_all_players()}
                    if message.text in players:
                        if players[message.text]:
                            if message.text != player.name:
                                mes = "Мафия выбрала жертву."
                                bot.send_message(config.channel, mes)

                                db_sess = db_session.create_session()
                                doctor = db_sess.query(Player).filter(Player.role == "doctor").first()

                                if doctor.alive:
                                    mes = "Доктор просыпается. Доктор, напишите мне в личные сообщения имя пациента."
                                    bot.send_message(config.channel, mes)
                                    var_dict["doctor_time"] = "True"
                                else:
                                    mes = "Доктор уже мертв... Комиссар, напишите мне в личные сообщения имя подозреваемого."
                                    bot.send_message(config.channel, mes)
                                    var_dict["commissar_time"] = "True"
                                var_dict["mafia_time"] = ""
                                var_dict["target"] = message.text
                                helpik.save_all_vars(var_dict)
                            else:
                                mes = "Вы не можете вальнуть себя!"
                                bot.send_message(message.chat.id, mes)
                        else:
                            mes = "Этот игрок уже мертв!"
                            bot.send_message(message.chat.id, mes)
                    else:
                        mes = "Такого игрока нет!"
                        bot.send_message(message.chat.id, mes)

                elif var_dict["doctor_time"] and player.role == "doctor":
                    if player.alive:
                        players = [player.name for player in helpik.get_all_players()]
                        if message.text in players:
                            mes = "Доктор сделал свой выбор."
                            bot.send_message(config.channel, mes)

                            if var_dict["target"] == message.text:
                                var_dict["target"] = ""

                            db_sess = db_session.create_session()
                            commissar = db_sess.query(Player).filter(Player.role == "commissar").first()

                            if commissar.alive:
                                mes = "Комиссар просыпается. Комиссар, напишите мне в личные сообщения имя подозреваемого."
                                bot.send_message(config.channel, mes)
                                var_dict["commissar_time"] = "True"
                                var_dict["doctor_time"] = ""
                                helpik.save_all_vars(var_dict)
                            else:
                                mes = "Комиссар уже мертв..."
                                bot.send_message(config.channel, mes)

                                mes = f"День {var_dict['day_n']}.\nГород просыпается."
                                bot.send_message(config.channel, mes)

                                if var_dict["target"]:
                                    mes = "Сегодня ночью был убит @" + var_dict["target"] + "."
                                    bot.send_message(config.channel, mes)

                                    db_sess = db_session.create_session()
                                    db_sess.query(Player).filter(Player.name == var_dict["target"]).update(
                                        {Player.alive: False})
                                    db_sess.commit()

                                    not_mafia_n = 0
                                    players = helpik.get_all_players()
                                    for m in players:
                                        if m.role != "mafia" and m.alive:
                                            not_mafia_n += 1
                                    if not_mafia_n <= 0:
                                        victory("mafia")
                                        return
                                else:
                                    mes = "Сегодня никто не пострадал!"
                                    bot.send_message(config.channel, mes)

                                mes = "Пришло время обсудить прошедшую ночь. " \
                                      "Когда будете готовы отправьте /stop_discussion."
                                bot.send_message(config.channel, mes)

                                var_dict["night"] = ""
                                var_dict["discussion"] = "True"
                                var_dict["target"] = ""
                                var_dict["day_n"] = str(int(var_dict["day_n"]) + 1)
                                helpik.save_all_vars(var_dict)

                        else:
                            mes = "Такого игрока нет!"
                            bot.send_message(config.channel, mes)

                elif var_dict["commissar_time"] and player.role == "commissar":
                    players = [player.name for player in helpik.get_all_players()]
                    if message.text in players:
                        db_sess = db_session.create_session()
                        commissar = db_sess.query(Player).filter(Player.role == "commissar").first()
                        if player.alive:
                            mes = "Комиссар сделал свой выбор."
                            bot.send_message(config.channel, mes)

                            maybe_mafia = db_sess.query(Player).filter(Player.name == message.text).first()

                            if maybe_mafia.role == "mafia":
                                mes = "Это мафия!."
                            else:
                                mes = "Вы ошиблись."
                            bot.send_message(message.chat.id, mes)

                        mes = f"День {var_dict['day_n']}.\nГород просыпается."
                        bot.send_message(config.channel, mes)

                        if var_dict["target"]:
                            mes = "Сегодня ночью был убит @" + var_dict["target"] + "."
                            bot.send_message(config.channel, mes)

                            db_sess = db_session.create_session()
                            db_sess.query(Player).filter(Player.name == var_dict["target"]).update({Player.alive: False})
                            db_sess.commit()

                            not_mafia_n = 0
                            players = helpik.get_all_players()
                            for m in players:
                                if m.role != "mafia" and m.alive:
                                    not_mafia_n += 1
                            if not_mafia_n <= 0:
                                victory("mafia")
                                return
                        else:
                            mes = "Сегодня никто не пострадал!"
                            bot.send_message(config.channel, mes)

                        mes = "Пришло время обсудить прошедшую ночь. " \
                              "Когда будете готовы отправьте /stop_discussion."
                        bot.send_message(config.channel, mes)

                        var_dict["night"] = ""
                        var_dict["commissar_time"] = ""
                        var_dict["discussion"] = "True"
                        var_dict["target"] = ""
                        var_dict["day_n"] = str(int(var_dict["day_n"]) + 1)
                        helpik.save_all_vars(var_dict)
                    else:
                        mes = "Такого игрока нет!"
                        bot.send_message(config.channel, mes)
                else:
                    bot.delete_message(message.chat.id, message.message_id)
                    mes = "Вы должны спать!"
                    bot.send_message(message.chat.id, mes)

            else:
                db_sess = db_session.create_session()
                player = db_sess.query(Player).filter(Player.name == message.from_user.username).first()

                if not var_dict["discussion"] or not player.alive:
                    bot.delete_message(message.chat.id, message.message_id)
                    if not player.alive:
                        mes = "Увы, мертвые не говорят..."
                    else:
                        mes = "Тсссссссс!"
                    bot.send_message(message.chat.id, mes)
        else:
            mes = "Вы не участвуете в игре, не мешайте процессу!"
            bot.send_message(config.channel, mes)


def check_admin(name):
    fl = False
    db_sess = db_session.create_session()
    for user in db_sess.query(User).filter(User.name == name):
        fl = True
    return fl


def victory(who_vin):
    if who_vin == "mafia":
        mes = "Мафия убила всех жителей города!\nВот эти маньяки сверху вниз:"

        db_sess = db_session.create_session()
        mafia = db_sess.query(Player).filter(Player.role == "mafia").all()
        for maf in mafia:
            mes += "\n@" + maf.name
    else:
        mes = "Жители города избавились от всей мафии, теперь можно спать спокойно!" \
              "\nХорошая игра, поздравляю с победой!"
    bot.send_message(config.channel, mes)

    mes = "Игра окончена."
    bot.send_message(config.channel, mes)
    #  сброс всех данных
    helpik.data_reset()


bot.polling()  # RUN

