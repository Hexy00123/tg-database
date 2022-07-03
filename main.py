import os
import psycopg2
import config
import telegram
import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

db_connection = psycopg2.connect(config.DB_URI, sslmode='require')
db_object = db_connection.cursor()

updater = Updater(config.BOT_TOKEN, use_context=True)
dp = updater.dispatcher


def get_keyboard(scheme: str, id):
    keyboard = [
        [
            InlineKeyboardButton(letter, callback_data=' ') for letter in [f'({id})', 'А', 'Б', 'В',
                                                                           'Г', 'Д', 'Е', 'Ж', 'З']
        ]
    ]
    for row in range(10):
        keyboard.append([InlineKeyboardButton(str(row + 1), callback_data=' ')] +
                        [InlineKeyboardButton(' ', callback_data=f'{row},{col}')
                         if scheme[row*7+col]=='1' else InlineKeyboardButton('🔴', callback_data=f'{row},{col}')

                         for col in range(7)])
    return keyboard

def start(update: Updater, context):
    msg: telegram.Message = update.message
    user_id = msg.from_user.id
    username = msg.from_user.username

    db_object.execute(f'select id from users where id={user_id}')
    result = db_object.fetchone()
    if not result:
        db_object.execute('INSERT INTO users(id, username, messages) VALUES (%s, %s, %s)', (user_id, username, 0))
        db_connection.commit()
        msg.reply_text(f'Added user\nid:{user_id}\nname:{username}')
        logger.info(f'added user {user_id} {username}')
    else:
        msg.reply_text(f'User {username} is exist')


def help(update, context):
    update.message.reply_text('Help!')


def debug(update, context):
    msg: telegram.Message = update.message
    msg.reply_text(str(eval(''.join(msg.text.split()[1:]))))


def create_matrix(update, context):
    user_id = update.message.from_user.id
    db_object.execute(f'select id from matrix')
    result = db_object.fetchall()
    new_id = 0
    if result:
        new_id = max(result, key=lambda x: x[0])[0] + 1

    db_object.execute('INSERT INTO matrix(id, user_id, info) VALUES (%s, %s, %s)', (new_id, user_id, '1' * 70))
    db_connection.commit()

    logger.info(f'new matrix - id = {new_id}, us_id = {user_id}')

    keyboard = get_keyboard('1' * 70, new_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f'id={new_id}', reply_markup=reply_markup)


def wrapper(update, context):
    query: Updater.query = update.callback_query
    if query.data!=' ':
        msg = query.message
        coords = list(map(int, query.data.split(',')))
        keyboard: InlineKeyboardMarkup = msg.reply_markup

        matrix_id = list(keyboard.inline_keyboard)[0][0]['text'][1:-1]
        db_object.execute(f'select info from matrix where id={matrix_id}')
        old_info = list(db_object.fetchone()[0])
        old_info[coords[0]*7+coords[1]] = '2' if old_info[coords[0]*7+coords[1]]=='1' else '1'
        old_info = ''.join(old_info)
        db_object.execute('update matrix set info = {} where id = {}'.format(old_info, matrix_id))
        db_connection.commit()

        logger.info(f'matrix {matrix_id} changed. coords: {coords}. value: {old_info[coords[0]*7+coords[1]]}')

        keyboard = get_keyboard(old_info, matrix_id)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=msg.text, reply_markup=reply_markup)
    query.answer()

def open_matrix(update, context):
    matrix_id = update.message.text.replace('/open_matrix ', '')
    db_object.execute(f'select info from matrix where id={matrix_id}')
    scheme = db_object.fetchone()[0]
    keyboard = get_keyboard(scheme, matrix_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text=f'id={matrix_id}', reply_markup=reply_markup)

def main():

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("debug", debug))
    dp.add_handler(CommandHandler("new_matrix", create_matrix))
    dp.add_handler(CommandHandler("open_matrix", open_matrix))
    dp.add_handler(CallbackQueryHandler(wrapper))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
  try:
    main()
  except Exception as e:
    logger.info(f'ERROR: {e}')
    
