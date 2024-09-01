import os
import telebot
import time
import random
import threading
from emoji import emojize
from telebot import types
from pymongo import MongoClient
import traceback
import config

token = ""
bot = telebot.TeleBot(token, num_threads = 50)

#astemiracle
#этот блок не трогать, подключение к локальной бд
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client.drunk
users = db.users
chats = db.chats

polls = {}
number = 0

try:
    users.find_one({'id': 242845840})['battlewin']
except:
    users.update_many({}, {'$set': {'battlewin': 0, 'battleloose': 0, 'draw': 0}})

symbols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'g', 'k', 'l', 'm', '1', '0', '9', '8', '6', '5', '4', '3', 'u',
           'o', 'x', 'q', 'r', 's', 't', 'u', 'v', 'w', 'y', 'z']

#astemiracle
#список переменных со значениями:

beercodes = [] #🍺 -1 к текущему хп
smokecodes = [] #🚬 0 пропускаем ход
healcodes = [] #💊 +1 к текущему хп
whiskeycodes = [] #🥃 -3 конкретные повреждения к хп


battles = {}
def randomgen():
    l = 10
    text = ''
    while len(text) < l:
        x = random.choice(symbols)
        if random.randint(1, 2) == 1:
            x = x.upper()
        text += x

    while text in beercodes or text in smokecodes or text in whiskeycodes:
        text = ''
        while len(text) < l:
            x = random.choice(symbols)
            if random.randint(1, 2) == 1:
                x = x.upper()
            text += x
    return text

while len(beercodes) < 100:
    key = randomgen()
    beercodes.append(key)

while len(smokecodes) < 100:
    key = randomgen()
    smokecodes.append(key)

while len(whiskeycodes) < 100:
    key = randomgen()
    whiskeycodes.append(key)

try:
    pass

except Exception as e:
    print('Ошибка:\n', traceback.format_exc())
    bot.send_message(242845840, traceback.format_exc())


def medit(message_text, chat_id, message_id, reply_markup=None, parse_mode=None):
    return bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text, reply_markup=reply_markup,
                                 parse_mode=parse_mode)

def createbattleplayer(user):
    return {
        'id': user.id,
        'score': 0,
        'name': user.first_name
    }


def createbattle(m, limit=3):
    global number
    player = createbattleplayer(m.from_user)
    a = {
        'players': {player['id']: player
                    },
        'id': m.chat.id,
        'scorelimit': limit,
        'number': number,
        'started': False,
        'turnresults': {},
        'kb': None,
        'beers': [],
        'whiskeys': [],
        'msgid': None,
        'turn': 1
    }

    number += 1
    return a

@bot.message_handler(func=lambda m: time.time() - m.date >= 120)
def skip(m):
    return


@bot.message_handler(commands=['testusers'])
def testusers(m):
    try:
        if m.from_user.id != 242845840:
            return
        bot.send_message(m.chat.id, 'Проверяю')
        us = 0
        ch = 0
        for ids in users.find({}):
            try:
                bot.send_chat_action(ids['id'], 'typing')
                us += 1
            except:
                pass
        for ids in chats.find({}):
            try:
                bot.send_chat_action(ids['id'], 'typing')
                ch += 1
            except:
                pass
        bot.send_message(242845840, 'Пользователи: ' + str(us) + '\nЧаты: ' + str(ch))
    except:
        pass

@bot.message_handler(commands=['sendm'])
def pinsendg(m):
    # config.about(m, bot)
    if m.from_user.id == 242845840:
        i = 0
        for ids in chats.find({}):
            try:
                time.sleep(0.1)
                bot.send_message(ids['id'], m.text.split('/sendm ')[1])
                i += 1
                if i % 100 == 0:
                    try:
                        bot.send_message(242845840, str(i) + ' чатов получили сообщение!')
                    except:
                        pass
            except:
                pass
        bot.send_message(242845840, str(i) + ' чатов получили сообщение!')

#astemiracle
#Блоки взаимодействия
@bot.message_handler(commands=['battle'])
def battlestart(m):
    try:
        try:
            limit = int(m.text.split()[1])
        except:
            limit = 3
        d = createbattle(m, limit)

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Принять вызов', callback_data='startduel?' + str(d['number'])))
        msg = bot.send_message(m.chat.id,
                               m.from_user.first_name + ' хочет сразиться в алкогольной дуэли! Здоровье: ' + str(
                                   limit) + '. Готовы принять вызов?', reply_markup=kb)
        d['msgid'] = msg.message_id
        battles.update({d['number']: d})
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data[:9] == 'startbattle')
def battlecall(call):
    try:
        battle = battles[int(call.data.split('?')[1])]
    except:
        print(traceback.format_exc())
        print(battles)
        return
    if battle['started']:
        bot.answer_callback_query(call.id, 'Битва уже началась')
        return
    if call.from_user.id in battle['players']:
        bot.answer_callback_query(call.id, 'Вы уже начали битву')
        return
    player = createbattleplayer(call.from_user)
    battle['players'].update({player['id']: player})
    battle['started'] = True
    text = battleedit(battle)

    kb, beers, whiskeys = getbeerkb(battle)

    battle['kb'] = kb
    battle['beers'] = beers
    battle['whiskeys'] = whiskeys

    medit(text, call.message.chat.id, call.message.message_id, reply_markup=kb)

#🍺 -1 к текущему хп
#🚬 0 пропускаем ход
#💊 +1 к текущему хп
#🥃 -3 конкретные повреждения к хп
@bot.callback_query_handler(func=lambda call: call.data[:4] == 'battle')
def battlecall2(call):
    time.sleep(random.randint(1, 10) / 100)
    try:
        battle = battles[int(call.data.split('?')[2])]
    except:
        return

    if call.from_user.id not in battle['players']:
        bot.answer_callback_query(call.id, 'Вы не участвуете в битве')
        return
    player = battle['players'][call.from_user.id]
    if call.from_user.id in battle['turnresults']:
        bot.answer_callback_query(call.id, 'Вы уже сделали выбор')
        return
    beer = call.data.split('?')[1]
    b = False
    w = False
    s = False
    if beer in beercodes:
        b = True
    elif beer in whiskeycodes:
        w = True
    else:
        s = True

    if b:
        text = '🍺|Пивка для рывка!'
        text2 = player['name'] + ': 🍺заказал(ла) кружку светлого\n'

        x = 'beer'
        result = 'found'
    elif w:
        text = '🥃|Это было лишним...'
        text2 = player['name'] + ': 🥃догнался(лась) крепким вискариком! Вызываем такси\n'

        x = 'whiskey'
        player['score'] += 9
        result = 'found'
    else:
        text = '🚬💨|Вы вышли перекурить!'
        text2 = player['name'] + ': 🚬💨вышел(ла) покурить\n'

        x = 'null'
        result = 'notfound'
    bot.answer_callback_query(call.id, text, show_alert=True)
    users.update_one({'id': player['id']}, {'$inc': {x: 1}})

    battle['turnresults'].update({player['id']: {'text': text2, 'result': result}})
    # medit(battleedit(duel), call.message.chat.id, call.message.message_id, reply_markup = duel['kb'])
    if len(battle['turnresults']) >= len(battle['players']):
        time.sleep(2)
        nextbattleturn(battle)

def nextduelturn(battle):
    notscore = True
    for ids in battle['turnresults']:
        if battle['turnresults'][ids]['result'] == 'notfound':
            notscore = False

    if not notscore:
        for ids in battle['turnresults']:
            if battle['turnresults'][ids]['result'] == 'found':
                battle['players'][ids]['score'] += 1

    end = False
    for ids in battle['players']:
        player = battle['players'][ids]
        if player['score'] >= battle['scorelimit']:
            end = True
    kb2 = types.InlineKeyboardMarkup()
    buttons1 = []
    buttons2 = []
    buttons3 = []
    i = 1
    while i <= 9:
        if i in battle['beers']:
            emoj = '🍺'
            if i in battle['whiskeys']:
                emoj = '🥃'
        else:
            emoj = '🚬'
        if i <= 3:
            buttons1.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        elif i <= 6:
            buttons2.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        elif i <= 9:
            buttons3.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        i += 1
    kb2.add(*buttons1)
    kb2.add(*buttons2)
    kb2.add(*buttons3)

    medit(battleedit(battle), v['id'], battle['msgid'], reply_markup=kb2)
    time.sleep(5)
    battle['turn'] += 1
    battle['turnresults'] = {}

    if end:
        endbattle(battle)
    else:
        kb, beers, whiskeys = getbattlekb(battle)
        battle['kb'] = kb
        battle['beers'] = beers
        battle['whiskeys'] = whiskeys

        text = battledit(battle)

        medit(text, battle['id'], battle['msgid'], reply_markup=kb)

def endbattle(battle):
    kb2 = types.InlineKeyboardMarkup()
    buttons1 = []
    buttons2 = []
    buttons3 = []
    i = 1
    while i <= 9:
        if i in battle['beers']:
            emoj = '🍺'
            if i in battle['whiskeys']:
                emoj = '🥃'
        else:
            emoj = '🚬'
        if i <= 3:
            buttons1.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        elif i <= 6:
            buttons2.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        elif i <= 9:
            buttons3.append(types.InlineKeyboardButton(text=emoj, callback_data='beer'))
        i += 1
    kb2.add(*buttons1)
    kb2.add(*buttons2)
    kb2.add(*buttons3)

    medit(battleedit(duel, endgame=True), duel['id'], duel['msgid'], reply_markup=kb2)
    try:
        del battles[battle['number']]
    except:
        pass

def battleedit(battle, endgame=False):
    text = 'Раунд ' + str(battle['turn']) + ':\n\n'
    for ids in battle['players']:
        player = battle['players'][ids]
        score = battle['score']
        if str(score)[-1] in ['1']:
            t = 'очко'
        elif str(score)[-1] in ['2', '3', '4']:
            t = 'очка'
        elif str(score)[-1] in ['0', '5', '6', '7', '8', '9']:
            t = 'очков'
        text += player['name'] + ': ' + str(player['score']) + '/' + str(battle['scorelimit']) + ' ' + t + '\n'
    text += '\n'
    if not endgame:
        for ids in battle['turnresults']:
            text += battle['turnresults'][ids]['text']
    else:
        winner = None
        players = []
        maxscore = -1000
        winner = None
        for ids in battle['players']:
            player = battle['players'][ids]
            if player['score'] > maxscore:
                maxscore = player['score']
                winner = player
            elif player['score'] == maxscore:
                winner = None
        if winner != None:
            for ids in battle['players']:
                if battle['players'][ids]['id'] != winner['id']:
                    looser = battle['players'][ids]
            text += '🏆 И победитель этой дуэли - ' + winner['name'] + '! Поздравляем!'
            users.update_one({'id': winner['id']}, {'$inc': {'duelwin': 1}})
            users.update_one({'id': looser['id']}, {'$inc': {'duelloose': 1}})
        else:
            text += 'Ничья!'
            for ids in battle['players']:
                users.update_one({'id': battle['players'][ids]['id']}, {'$inc': {'draw': 1}})

    return text


