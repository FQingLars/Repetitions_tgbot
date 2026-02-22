import os.path
import logging
import time
import threading
import json
from flask import Flask, request, send_from_directory

from telebot import TeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
import datetime

from config import APIKEY
from dbfuncs import *
from db_autocleaner import autocleaner


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                    handlers=[logging.FileHandler(f"Logs/app{int(time.time())}.log", encoding='utf-8'),
                              logging.StreamHandler()])
bot = TeleBot(token=APIKEY)

app = Flask(__name__)
WEB_PORT = 5000

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/schedule')
def get_schedule_api():
    reps = select_rasp()
    data = []
    for group, time_obj in reps:
        data.append({
            "group": group,
            "datetime": time_obj.strftime('%Y-%m-%d %H:%M')
        })
    return json.dumps(data, ensure_ascii=False)


@app.route('/webhook', methods=['POST'])
def webhook():
    return "OK", 200


def run_flask():
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)

@bot.message_handler(func=lambda message: message.text in ("/start", "Повторить🔁"))
def start(message):
    kb = InlineKeyboardMarkup()
    bttns = (InlineKeyboardButton(text="Добавить репу➕", callback_data="add_rep"),
             InlineKeyboardButton(text="Удалить репу➖", callback_data="del_rep"),
             InlineKeyboardButton(text="Посмотреть репы🍳", callback_data="show_rep"),
             InlineKeyboardButton(text="Открыть Web App 🌐", web_app=types.WebAppInfo(
                 url="https://твоя-ссылка-ngrok.ngrok.io")))

    # Добавляем кнопку Web App в меню
    kb.add(bttns[0], bttns[1]).add(bttns[2]).add(bttns[3], bttns[4]).add(bttns[5])

    bot.send_message(message.chat.id, "Бот для расписания репетиций. Выберите опцию:", reply_markup=kb)

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        text_data = data.get('text_data')

        fake_msg = type('obj', (object,), {'text': text_data, 'chat': message.chat, 'from_user': message.from_user})

        if action == 'add':
            request_rep_add(fake_msg, message.from_user.id, message.chat.id)
        elif action == 'delete':
            request_rep_del(fake_msg, message.from_user.id, message.chat.id)

    except Exception as e:
        logging.error(f"Ошибка обработки Web App данных: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке заявки.")

@bot.callback_query_handler(func=lambda call: call.data in ("add_rep", "del_rep", "show_rep", "add_admin", "del_admin"))
def user_board(call):
    bot.answer_callback_query(call.id)
    message = call.message

    match call.data:
        case "add_rep":
            msg = bot.send_message(message.chat.id,
                                   "Напишите данные для записи в формате:\n\n{Название группы}\n{Дата и время в формате DD.mm.YYYY HH:MM}")
            user_id = call.from_user.id
            chat_id = message.chat.id

            def handle_rep_input(mes: Message):
                request_rep_add(mes, user_id, chat_id)

            bot.register_next_step_handler(msg, handle_rep_input)
        case "del_rep":
            msg = bot.send_message(message.chat.id,
                                   "Напишите данные для записи в формате:\n\n{Название группы}\n{Дата и время в формате DD.mm.YYYY HH:MM}")
            user_id = call.from_user.id
            chat_id = message.chat.id

            def handle_rep_input(mes: Message):
                request_rep_del(mes, user_id, chat_id)

            bot.register_next_step_handler(msg, handle_rep_input)
        case "show_rep":
            reps = select_rasp()
            reps.sort(key=lambda x: x[1])
            text = "Расписание:\n\n"

            for group, time in reps:
                # time - это объект datetime
                time_str = time.strftime('%d.%m.%Y %H:%M')
                text += f"{time_str}: {group}\n"

            bot.send_message(message.chat.id, text if text != "Расписание:\n\n" else "Репетиций нет.")
        case "add_admin":
            if not check_admin(call.from_user.id):
                logging.warning(f"Пользователь с ID {call.from_user.id} попытался использовать панель админа.")
                bot.answer_callback_query(call.id, "У вас недостаточно прав для этого.")
                return

            msg = bot.send_message(message.chat.id,
                                   "Введите chat id человека для добавления его в админы. Узнать его можно, переслав его сообщение этому боту: @GetChatID_IL_BOT.")
            bot.register_next_step_handler(msg, add_admin)
        case "del_admin":
            if not check_admin(call.from_user.id):
                logging.warning(f"Пользователь с ID {call.from_user.id} попытался использовать панель админа.")
                bot.answer_callback_query(call.id, "У вас недостаточно прав для этого.")
                return

            msg = bot.send_message(message.chat.id,
                                   "Введите chat id человека для удаления его из админов. Узнать его можно, переслав его сообщение этому боту: @GetChatID_IL_BOT.")
            bot.register_next_step_handler(msg, del_admin)


def request_rep_add(message: Message, user_id: int, chat_id: int):
    text = message.text

    lines = text.split("\n")
    if len(lines) != 2:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(chat_id, "Неверный формат данных. Попробуйте снова.", reply_markup=kb)
        return

    group, time_str = lines

    try:
        time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M')
    except ValueError as e:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(chat_id, "Неверный формат даты. Используйте DD.mm.YYYY HH:MM.", reply_markup=kb)
        logging.exception(f"Возникла ValueError: {e}.")
        return

    if check_admin(user_id):
        bot.send_message(chat_id, "Запрос на добавление записи отправлен админам.")

        admins = select_admins()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("Принять✔", callback_data="accept"),
               InlineKeyboardButton("Отклонить❌", callback_data="reject"),
               InlineKeyboardButton("Изменить дату и время🔁", callback_data="edit_rep"))

        for admin_id in admins:
            source = "🌐 Web App"
            bot.send_message(admin_id, f"Поступил запрос ({source}) на репетицию:\n\n{text}", reply_markup=kb)
            logging.info(f"Запрос на добавление репетиции отправлен: {admin_id}.")
    else:
        insert_rep(group, time)
        bot.send_message(chat_id, "Запись успешно добавлена!")
        logging.info(f"Запись на репетицию добавлена: {group}, {time}.")


@bot.callback_query_handler(func=lambda call: call.data == "accept")
def accept(call):
    bot.answer_callback_query(call.id)
    try:
        text = call.message.text.split("\n")
        group, time_str = text[-2], text[-1]

        time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M')

        insert_rep(group, time)
        bot.send_message(call.message.chat.id, "Запись успешно добавлена в расписание✔")
        logging.info(f"Запись на репетицию добавлена: {group}, {time}.")
    except Exception as e:
        logging.exception(f"Ошибка при принятии запроса: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "reject")
def reject(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Запрос на запись отклонен❌")
    logging.info(f"Запись на репетицию отклонена.")


@bot.callback_query_handler(func=lambda call: call.data == "edit_rep")
def edit_rep(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
                           "Введите измененные данные для записи в формате:\n\n{Название группы}\n{Дата и время в формате DD.mm.YYYY HH:MM}")
    bot.register_next_step_handler(msg, edit_rep_handler)


def edit_rep_handler(message: Message):
    text = message.text.strip()
    lines = text.split("\n")
    if len(lines) != 2:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        msg = bot.send_message(message.chat.id, "Неверный формат данных. Попробуйте снова.", reply_markup=kb)
        bot.register_next_step_handler(msg, edit_rep_handler)
        return

    group, time_str = lines
    try:
        time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M')
    except ValueError as e:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        msg = bot.send_message(message.chat.id, "Неверный формат даты. Используйте DD.mm.YYYY HH:MM.", reply_markup=kb)
        logging.exception(f"Возникла ValueError: {e}.")
        bot.register_next_step_handler(msg, edit_rep_handler)
        return

    insert_rep(group, time)
    bot.send_message(message.chat.id, "Измененная запись успешно добавлена!")
    logging.info(f"Запись на репетицию изменена и добавлена: {group}, {time}.")


def request_rep_del(message: Message, user_id: int, chat_id: int):
    text = message.text
    lines = text.split("\n")
    if len(lines) != 2:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(chat_id, "Неверный формат данных. Попробуйте снова.", reply_markup=kb)
        return

    group, time_str = lines
    try:
        time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M')
    except ValueError:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(chat_id, "Неверный формат даты. Используйте DD.mm.YYYY HH:MM.", reply_markup=kb)
        return

    if not check_admin(user_id):
        bot.send_message(chat_id, "Запрос на удаление записи отправлен админам.")
        admins = select_admins()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton("Принять✔", callback_data="accept_del"),
               InlineKeyboardButton("Отклонить❌", callback_data="reject_del"))

        for admin_id in admins:
            bot.send_message(admin_id, f"Поступил запрос на удаление репетиции:\n\n{text}", reply_markup=kb)
    else:
        delete_rep(group, time)
        bot.send_message(chat_id, "Запись успешно удалена!")
        logging.info(f"Запись на репетицию удалена: {group}, {time}.")


@bot.callback_query_handler(func=lambda call: call.data == "accept_del")
def accept_del(call):
    bot.answer_callback_query(call.id)
    text = call.message.text.split("\n")
    group, time_str = text[-2], text[-1]
    time = datetime.datetime.strptime(time_str, '%d.%m.%Y %H:%M')
    delete_rep(group, time)
    bot.send_message(call.message.chat.id, "Запись успешно удалена из расписания✔")
    logging.info(f"Запись на репетицию удалена: {group}, {time}.")


@bot.callback_query_handler(func=lambda call: call.data == "reject_del")
def reject_del(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Запрос на удаление записи отклонен❌")
    logging.info(f"Запрос отклонен: {call.message.chat.id}.")


def add_admin(message: Message):
    try:
        id = int(message.text)
    except:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(message.chat.id, "Неверные данные. Попробуйте еще раз.", reply_markup=kb)
        return
    insert_admin(id)
    bot.send_message(message.chat.id, "Админ успешно добавлен✔.")
    logging.info(f"Добавлен админ: {id}.")


def del_admin(message: Message):
    try:
        id = int(message.text)
    except:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("Повторить🔁"))
        bot.send_message(message.chat.id, "Неверные данные. Попробуйте еще раз.", reply_markup=kb)
        return

    if not check_primary_admin(id):
        delete_admin(id)
        bot.send_message(message.chat.id, "Админ успешно удален✔.")
        logging.info(f"Админ удален: {id}.")
    else:
        bot.send_message(message.chat.id, "Невозможно удалить первичного админа❌.")
        logging.info(f"Попытка удаления первичного админа от {message.from_user.id}.")


if __name__ == "__main__":
    if not os.path.isfile("repdatabase.db"):
        primary_admin = int(input("Введите chat id первичного админа...\n"))
        db_init(primary_admin)

    autocleaner()

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logging.info("Бот и Web Server запущены.")
    bot.infinity_polling(skip_pending=True, logger_level=logging.INFO)