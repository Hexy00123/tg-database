import os
import logging
import config
import telegram
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler

def start(update, context):
    update.message.reply_text('Hi!')

def help(update, context):
    update.message.reply_text('Help!')

def main():
    updater = Updater(config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    if config.APP_URL is None:
        updater.start_polling()  # врубает бота с локалки
    else:
        updater.start_webhook(listen='0.0.0.0', port=int(os.environ.get('PORT', 5000)), url_path=config.BOT_TOKEN)
        updater.bot.set_webhook(config.APP_URL)  # врубает бота с сервера
    updater.idle()  # ==while True


if __name__ == '__main__':
    main()