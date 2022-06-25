import psycopg2
import config
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler

db_connection = psycopg2.connect(config.DB_URI, sslmode='require')
db_object = db_connection.cursor()

updater = Updater(config.BOT_TOKEN, use_context=True)
dp = updater.dispatcher


def start(update: Updater, context):
    msg: telegram.Message = update.message
    user_id = msg.from_user.id
    username = msg.from_user.username

    db_object.execute(f'select id from users where id={user_id}')
    result = db_object.fetchone()
    if not result:
        db_object.execute(f'insert into users(id, username, messages) values ({user_id}, {username}, 0)')

    msg.reply_text(f'Добавлен пользователь\nid:{user_id}\nusername:{username}')



def help(update, context):
    update.message.reply_text('Help!')

def debug(update, context):
    msg: telegram.Message = update.message
    msg.reply_text(eval(msg.text))

def main():
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("debug", debug))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
