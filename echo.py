#!/usr/bin/env python
# coding=utf-8

import logging
import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)
telebot.logger.setLevel(logging.DEBUG)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hola, ¿qué haces?")


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.polling()