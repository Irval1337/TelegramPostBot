# -*- coding: utf-8 -*-
from telebot import *
import datetime
from time import sleep
from dateutil import parser
import json
from threading import Thread

class Hide:
    def __init__(self, text, title, id, **kwargs):
        self.text = text
        self.title = title
        self.id = id
        self.attribute = kwargs or None

    def getText(self):
        return self.text

    def getTitle(self):
        return self.title

    def getId(self):
        return self.id

class Post:
    def __init__(self, text, hides, time, **kwargs):
        self.text = text
        self.hides = hides
        self.time = time
        self.attribute = kwargs or None

    def getText(self):
        return self.text

    def getHides(self):
        return self.hides

    def getTime(self):
        return self.time

class PostEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Post) or isinstance(obj, Hide):
            return obj.__dict__
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y.%m.%d %H:%M")
        return json.JSONEncoder.default(self, obj)

bot = telebot.TeleBot('') # Токен бота
chatId = 0 # Id канала для публикации
admin = "" # Ник администратора
posts = list()
planned = list()
adminStage = 0
currentText = ""
currentTime = datetime.datetime.now()
currentHides = list()
hidesMessage = 0

try:
    f = open('data.json')
    info = json.loads(f.read())
    for post in info:
        hides = list()
        for hide in post["hides"]:
            newHide = Hide(hide["text"], hide["title"], hide["id"])
            hides.append(newHide)
        newPost = Post(post["text"], hides, parser.parse(post["time"]))
        posts.append(newPost)
except:
    print("Parsing error")

currentTitle = ""
currentHideText = ""

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global adminStage, admin, posts, planned, hidesMessage
    global currentText, currentHides, currentTime
    global chatId
    global currentTitle, currentHideText

    if message.chat.type == "private" and message.from_user.username == admin:
        if message.text == "/start" or message.text == "Отмена":
            mm = types.ReplyKeyboardMarkup(row_width=2)
            button = types.KeyboardButton("Создать новую запись")
            mm.add(button)
            button1 = types.KeyboardButton("История публикаций")
            button2 = types.KeyboardButton("Отложенные посты")
            mm.add(button1, button2)
            bot.send_message(message.from_user.id, "Вас приветствует бот для публикации защищенных от парсинга сообщений.", reply_markup=mm)
            adminStage = 0
        elif message.text == "Создать новую запись":
            mm = types.ReplyKeyboardMarkup(row_width=1)
            button = types.KeyboardButton("Отмена")
            mm.add(button)
            bot.send_message(message.from_user.id, "Укажите текст публикуемой записи:", reply_markup=mm)
            adminStage = 1
        elif message.text == "История публикаций":
            doc = open('log.txt', 'rb')
            bot.send_document(message.chat.id, doc)
        elif message.text == "Отложенные посты":
            key = types.InlineKeyboardMarkup()
            i = 0
            for post in planned:
                but = types.InlineKeyboardButton(text=post.getText(), callback_data="DeletePost_" + str(i))
                key.add(but)
                i += 1
            bot.send_message(message.from_user.id, "Выберите пост для удаления:", reply_markup=key)
        else:
            if adminStage == 0:
                bot.send_message(message.from_user.id, "Неизвестная команда")
            elif adminStage == 1:
                currentText = message.text
                key = types.InlineKeyboardMarkup()
                but = types.InlineKeyboardButton(text="Далее", callback_data="NextHide")
                key.add(but)
                but = types.InlineKeyboardButton(text="Добавить", callback_data="AddHide")
                key.add(but)
                hidesMessage = bot.send_message(message.from_user.id, "Измените прикрепленные к записи спойлеры:", reply_markup=key)
                adminStage = 2
            elif adminStage == 4:
                datetime_object = parser.parse(message.text)
                posts.append(Post(currentText, currentHides, datetime_object))
                planned.append(posts[len(posts) - 1])
                mm = types.ReplyKeyboardMarkup(row_width=2)
                button = types.KeyboardButton("Создать новую запись")
                mm.add(button)
                button1 = types.KeyboardButton("История публикаций")
                button2 = types.KeyboardButton("Отложенные посты")
                mm.add(button1, button2)
                saveData()
                bot.send_message(message.chat.id, "Запись успешно запланирована", reply_markup=mm)
                printer("Запланирована новая запись")
                adminStage = 0
                currentHides = list()
            elif adminStage == 5:
                currentTitle = message.text
                bot.send_message(message.from_user.id, "Укажите отображаемый текст:")
                adminStage = 6
            elif adminStage == 6:
                currentHideText = message.text
                hide = Hide(currentHideText, currentTitle, str(len(posts)) + "_" + str(len(currentHides)))
                currentHides.append(hide)
                key = hidesMessage.reply_markup
                but = types.InlineKeyboardButton(text=currentTitle, callback_data="editHide_" + hide.getId())
                key.add(but)
                hidesMessage = bot.edit_message_reply_markup(hidesMessage.chat.id, hidesMessage.message_id, reply_markup=key)
                adminStage = 2
                bot.send_message(message.from_user.id, "Спойлер успешно добавлен")
@bot.callback_query_handler(func=lambda c:True)
def inline(c):
    global adminStage, admin, posts, hidesMessage
    global currentText, currentHides, currentTime
    global chatId
    global planned

    if c.data == "NextHide" and adminStage == 2:
        key = types.InlineKeyboardMarkup()
        but1 = types.InlineKeyboardButton(text="Да", callback_data="YesTime")
        but2 = types.InlineKeyboardButton(text="Опубликовать сейчас", callback_data="NoTime")
        key.add(but1, but2)
        bot.send_message(c.message.chat.id, "Опубликовать запись в определенное время?", reply_markup=key)
        adminStage = 3
    if c.data == "AddHide" and adminStage == 2:
        bot.send_message(c.message.chat.id, "Укажите заголовок спойлера:")
        adminStage = 5
    elif c.data == "YesTime" and adminStage == 3:
        bot.send_message(c.message.chat.id, "Укажите время публикации в формате dd.mm.yyyy hh:mm:")
        adminStage = 4
    elif c.data == "NoTime" and adminStage == 3:
        posts.append(Post(currentText, currentHides, datetime.datetime.now()))
        key = types.InlineKeyboardMarkup()
        for hide in currentHides:
            but = types.InlineKeyboardButton(text=hide.getTitle(), callback_data="showHide_" + hide.getId())
            key.add(but)
        bot.send_message(chatId, currentText, reply_markup=key)

        mm = types.ReplyKeyboardMarkup(row_width=2)
        button = types.KeyboardButton("Создать новую запись")
        mm.add(button)
        button1 = types.KeyboardButton("История публикаций")
        button2 = types.KeyboardButton("Отложенные посты")
        mm.add(button1, button2)
        saveData()
        currentHides = list()
        bot.send_message(c.message.chat.id, "Запись успешно опубликована", reply_markup=mm)
        printer("Опубликована новая запись")
        adminStage = 0
    elif str(c.data).startswith("editHide_"):
        newHides = list()
        key = types.InlineKeyboardMarkup()
        but = types.InlineKeyboardButton(text="Далее", callback_data="NextHide")
        key.add(but)
        but = types.InlineKeyboardButton(text="Добавить", callback_data="AddHide")
        key.add(but)
        for hide in currentHides:
            if "editHide_" + hide.getId() != str(c.data):
                newHides.append(hide)
                but = types.InlineKeyboardButton(text=hide.getTitle(), callback_data="editHide_" + hide.getId())
                key.add(but)
        currentHides = newHides
        hidesMessage = bot.edit_message_reply_markup(hidesMessage.chat.id, hidesMessage.message_id, reply_markup=key)
        bot.send_message(c.message.chat.id, "Спойлер успешно удален")
    elif str(c.data).startswith("showHide_"):
        data = str(c.data).split("_")
        first = int(data[1])
        second = int(data[2])
        bot.answer_callback_query(callback_query_id=c.id, text=posts[first].getHides()[second].getText(), show_alert=True)
    elif str(c.data).startswith("DeletePost_"):
        data = str(c.data).split("_")
        index = int(data[1])
        posts.remove(planned[index])
        planned.remove(planned[index])
        bot.send_message(c.message.chat.id, "Запись успешно удалена")
        printer("Удалена запланированная запись")

def saveData():
    f = open('data.json', 'w')
    f.write(json.dumps(posts, indent=4, cls=PostEncoder))
    printer("Данные о постах записаны в файл")

def checkPlanned(*args, **kwargs):
    while True:
        global planned
        for post in planned:
            time = post.getTime()
            if datetime.datetime.now() >= time:
                key = types.InlineKeyboardMarkup()
                for hide in post.getHides():
                    but = types.InlineKeyboardButton(text=hide.getTitle(), callback_data="showHide_" + hide.getId())
                    key.add(but)
                bot.send_message(chatId, currentText, reply_markup=key)
                printer("Опубликована новая запись")
                planned.remove(post)
        sleep(1)

def printer(printing):
    log_file = open("log.txt", "a")
    log_file.write("[" + str(datetime.datetime.now()) + "] " + str(printing) + '\n')
    log_file.close()
    return printer

th = Thread(target=checkPlanned, args=())
th.start()
bot.polling(none_stop=True, interval=0)
