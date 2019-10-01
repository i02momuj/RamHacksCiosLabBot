#!/usr/bin/env python
# coding=utf-8

import logging
from config import TOKEN
import request

import telegram
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import ForceReply
import telebot
import re
from datetime import datetime

import math

from telebot import types

from SQLmanager import *


bot = telebot.TeleBot(TOKEN)
telebot.logger.setLevel(logging.DEBUG)

#queue = []
reply_to = None

def check_response(): return lambda message: chat.Chat.get(message)

#
# Handle replied messages
#
@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def echo_all(message):
    if "Reservation" in message.reply_to_message.text:
        reserve(message.chat.id, message.text)
    elif "Modification" in message.reply_to_message.text:
        modify(message.chat.id, message.text)
    elif "Checking" in message.reply_to_message.text:
        check(message.chat.id, message.text)


#
# Handles /start and /help commands
#
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to HackRamsCiosLabBot! You can use */reserve*, */check*, */modify*, and */cancel* commands to interact with me.", parse_mode = "Markdown")
    #bot.send_message(message.chat.id, "You will be able to *reserve* a parking slot for the future, to *check* current availability, to *modify* your current reservation, or to *cancel* a previous reservation.", parse_mode = "Markdown")

    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('/reserve')
    itembtn2 = types.KeyboardButton('/check')
    itembtn3 = types.KeyboardButton('/modify')
    itembtn4 = types.KeyboardButton('/cancel')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    bot.send_message(message.chat.id, "You will be able to *reserve* a parking slot for the future, to *check* current availability, to *modify* your current reservation, or to *cancel* a previous reservation.", parse_mode = "Markdown", reply_markup=markup)


#
# Handles /reserve command
#
@bot.message_handler(regexp='^[Rr]eserve')
def reserve_handle(message):
    #bot.reply_to(message, "Trying to reserve a parking slot. Enter your start time:")
    #reserve_handle(message.chat.id, message)
    regex = re.search(r'^[\/]?[Rr]eserve\s+(\d\d?(.|:)\d\d\s?){2,}', message.text)
    
    if regex is None:
        bot.send_message(message.chat.id, "Please, introduce the start and end hours to reserve the parking slot.")
        return None

    reserve(message.chat.id, message.text)

@bot.message_handler(commands=['reserve'])
def reserve_handle_command(message):
    markup = types.ForceReply(selective=False)
    bot.reply_to(message, "Reservation. Please, introduce the _start_ and _end_ hours. For example: \"9:00 14:30\"", parse_mode = "Markdown", reply_markup=markup)
    

#
# Handles /modify command
#
@bot.message_handler(regexp='^[Mm]odify')
@bot.message_handler(commands=['modify'])
def modify_handle_command(message):
    regex = re.search(r'^[\/]?[Mm]odify\s?\d+:', message.text)
    
    if regex is not None:
        id = message.text.split(":")[0].split(" ")[1]
        markup = types.ForceReply(selective=False)
        bot.reply_to(message, "Modification " + str(id) + ". Please, introduce the new _start_ and _end_ hours. For example: \"9:00 14:30\"", parse_mode = "Markdown", reply_markup=markup)

    else:
        print_reservations(message, '/modify', "Click on the reservation you want to modify.")

    

#
# Handles /check command
#
@bot.message_handler(regexp='^[Cc]heck')
def check_handle(message):
    regex = re.search(r'^[\/]?[Cc]heck\s?((\d\d?(.|:)\d\d\s?){1,2})', message.text)
    
    if regex is None:
        bot.send_message(message.chat.id, "Please, introduce the end hour to check the availability of parking slots.")
        return None

    check(message.chat.id, message.text)

@bot.message_handler(commands=['check'])
def check_handle_command(message):
    markup = types.ForceReply(selective=False)
    bot.reply_to(message, "Checking. Please, introduce the _end_ hour to check availability from now. For example: \"14:30\"", parse_mode = "Markdown", reply_markup=markup)
    

#
# Handles /cancel command
#
@bot.message_handler(regexp='^[Cc]ancel')
@bot.message_handler(commands=['cancel'])
def cancel_handle(message):
    regex = re.search(r'^[\/]?[Cc]ancel\s?\d+:', message.text)
    
    if regex is not None:
        id = message.text.split(":")[0].split(" ")[1]
        cancel(message.chat.id, int(id))
    else:
        print_reservations(message, '/cancel', "Click on the reservation you want to delete.")


def print_reservations(message, command, text):
    #cancel(message.chat.id)
    chat_id = message.chat.id

    reservations = get_reservation(chat_id)

    markup = types.ReplyKeyboardMarkup(row_width=1)
    items = []

    n_reservations = len(reservations)
    if n_reservations > 0:
        for i in range(0, len(reservations)):
            item = types.KeyboardButton(command + " " + str(reservations[i][0]) + ": " + str(reservations[i][1]) + " - " + str(reservations[i][2]))
            items.append(item)
    else:
        send_message("Sorry, you hadn't any slot reserved.", chat_id)
        return None

    if n_reservations == 1:
        markup.add(items[0])
    elif n_reservations == 2:
        markup.add(items[0], items[1])
    elif n_reservations == 3:
        markup.add(items[0], items[1], items[2])
    elif n_reservations == 4:
        markup.add(items[0], items[1], items[2], items[3])
    elif n_reservations >= 5:
        markup.add(items[0], items[1], items[2], items[3], items[4])

    bot.send_message(chat_id, text, parse_mode = "Markdown", reply_markup=markup)

#
# Send message to an user
#
def send_message(text, chat_id, markup=None):
    if markup is None:
        bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, text, markup)

#
# Handles the reservation of a slot
#
def reserve(chat_id, text):
    hour1 = None
    hour2 = None
    now = datetime.now()

    words = text.split(" ")
    if len(words) == 2:
        hour1_str = words[0]
        hour2_str = words[1]
    elif len(words) == 3:
        hour1_str = words[1]
        hour2_str = words[2]
    else:
        send_message("Please, introduce only the start and end hours to reserve the parking slot.", chat_id)
        return None

    if "." in hour1_str and len(hour1_str) > 1:
        hour1 = datetime.strptime(hour1_str, '%H.%M')
    elif ":" in hour1_str:
        hour1 = datetime.strptime(hour1_str, '%H:%M')

    if "." in hour2_str and len(hour2_str) > 1:
        hour2 = datetime.strptime(hour2_str, '%H.%M')
    elif ":" in hour1_str:
        hour2 = datetime.strptime(hour2_str, '%H:%M')

    if hour1 is not None and hour2 is not None:
        hour1 = now.replace(minute=hour1.minute).replace(hour=hour1.hour).replace(second=hour1.second)
        hour2 = now.replace(minute=hour2.minute).replace(hour=hour2.hour).replace(second=hour2.second)
        if hour1 >= hour2:
            send_message("Please, introduce the hours in correct order.", chat_id)
        else:
            slot = get_availability(hour1, hour2)
            duplicated = check_duplication(chat_id, hour1, hour2)

            if slot > 0:
                if duplicated <= 0:
                    if reserve_space(chat_id, hour1, hour2) > 0:
                        send_message("Parking slot reserved from " + str(hour1.hour) + ":" + str(hour1.minute) + " to " + str(hour2.hour) + ":" + str(hour2.minute), chat_id)
                        bot.send_photo(chat_id=chat_id, photo=open('qrcode.png', 'rb'))
                    else:
                        send_message("An error occurred. Please, try again later.", chat_id)
                else:
                    send_message("You already have a reserved slot at these hours.", chat_id)
            elif slot < 0:
                send_message("There is no space available for the given hours.", chat_id)
            else:
                send_message("At this moment we have not available spaces, but we are working on it. Please, try it again later.", chat_id)
                #global queue
                #queue.append([chat_id, hour1, hour2])
                #employees = getEmployees()
                #nContact = math.ceil(len(employees)*.1)
                #for i in range(0, nContact):
                #    send_message("Please, cancel or modify your parking slot if you are not going to use it.", employees[i])

#
# Handles the modification of a reservation
#
def modify(chat_id, text):
    hour1 = None
    hour2 = None
    now = datetime.now()

    words = text.split(" ")
    if len(words) == 2:
        hour1_str = words[0]
        hour2_str = words[1]
    elif len(words) == 3:
        hour1_str = words[1]
        hour2_str = words[2]
    else:
        send_message("Please, introduce only the start and end hours to reserve the parking slot.", chat_id)
        return None

    if "." in hour1_str and len(hour1_str) > 1:
        hour1 = datetime.strptime(hour1_str, '%H.%M')
    elif ":" in hour1_str:
        hour1 = datetime.strptime(hour1_str, '%H:%M')

    if "." in hour2_str and len(hour2_str) > 1:
        hour2 = datetime.strptime(hour2_str, '%H.%M')
    elif ":" in hour1_str:
        hour2 = datetime.strptime(hour2_str, '%H:%M')

    if hour1 is not None and hour2 is not None:
        hour1 = now.replace(minute=hour1.minute).replace(hour=hour1.hour).replace(second=hour1.second)
        hour2 = now.replace(minute=hour2.minute).replace(hour=hour2.hour).replace(second=hour2.second)
        if hour1 >= hour2:
            send_message("Please, introduce the hours in correct order.", chat_id)
        else:
            if update_reservation(chat_id, hour1, hour2) > 0:
                send_message("The reservation of your slot was modified from " + str(hour1.hour) + ":" + str(hour1.minute) + " to " + str(hour2.hour) + ":" + str(hour2.minute), chat_id)
                #notifyQueue()
            else:
                send_message("Sorry, you hadn't any slot reserved.", chat_id)

#
# Handles the check availability functionality
#
def check(chat_id, text):
    hour1 = None
    now = datetime.now()

    words = text.split(" ")
    if len(words) == 1:
        hour1_str = words[0]
    elif len(words) == 2:
        hour1_str = words[1]
    else:
        send_message("Please, introduce only the end hour to check slot availability.", chat_id)
        return None

    if "." in hour1_str and len(hour1_str) > 1:
        hour1 = datetime.strptime(hour1_str, '%H.%M')
    elif ":" in hour1_str:
        hour1 = datetime.strptime(hour1_str, '%H:%M')
    
    if hour1 is not None:
        hour1 = now.replace(minute=hour1.minute).replace(hour=hour1.hour).replace(second=hour1.second)
        now = datetime.now()
        slot = get_availability(now, hour1)

        if slot > 0:
            send_message("There is parking slot available from now until " + str(hour1.hour) + ":" + str(hour1.minute), chat_id)
        elif slot < 0:
            send_message("There is no space available for the given hours.", chat_id)
        else:
            send_message("At this moment we have not available spaces, but we are working on it. Please, try it again later.", chat_id)
            #global queue
            #queue.append([chat_id, 0, hour1])
            #employees = getEmployees()
            #nContact = math.ceil(len(employees)*.1)
            #for i in range(0, nContact):
            #    send_message("Please, cancel or modify your parking slot if you are not going to use it.", employees[i])


#
# Handles the cancelation of a reservation
#
def cancel(chat_id, id):
    count =  cancel_reservation(chat_id, id)
    if count > 0:
        send_message("Your slot was cancelled.", chat_id)
    else:
        send_message("Sorry, you hadn't any slot reserved.", chat_id)
        


def notifyQueue():
    global queue
    for guest in queue:
        if(check_reservation1(guest[1], guest[2])):
            queue.remove(guest)
            send_message("Now you can reserve a new space.", guest[0])
            break


bot.polling()
