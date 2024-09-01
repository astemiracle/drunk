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
mongo_client = MongoClient(os.environ['database'])
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


duels = {}
def randomgen():
    l = 10
    text = ''
    while len(text) < l:
        x = random.choice(symbols)
        if random.randint(1, 2) == 1:
            x = x.upper()
        text += x

    while text in dickcodes or text in emptycodes or text in golddickcodes:
        text = ''
        while len(text) < l:
            x = random.choice(symbols)
            if random.randint(1, 2) == 1:
                x = x.upper()
            text += x
    return text