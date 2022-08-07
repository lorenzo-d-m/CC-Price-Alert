"""
Author: Lorenzo
Date: 31/07/2022

Simple Telegram bot triggered by cryptocurrency stop-prices.
"""

__version__  = 0.1

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from telegram.ext import CallbackContext
import logging
from custom.api_keys import TELEGRAM_BOT_API_KEY
from cmc import *

# TODO check user id

bot = telegram.Bot(token=TELEGRAM_BOT_API_KEY)
print(bot.get_me())

updates = bot.get_updates()
#print(updates[0])
#bot.send_message(text='Sell baby!', chat_id=622124736)

# Updater (it listens for messages)--> queue (uncontrollable) --> Dispatcher (controlled by handler)
updater = Updater(token=TELEGRAM_BOT_API_KEY, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


### Service funcions ###
def background_price_check(symbol, upper_sp, lower_sp, update: Update, context: CallbackContext):
    import time
    from cmc import get_price

    
    price = get_price(symbol) #get real time price
    print(f'{symbol} @${price}. Upper sp: ${upper_sp}, Lower sp: ${lower_sp} -', \
        'Time:', time.strftime("%a, %d, %b, %Y, %X, GMT+0000", time.gmtime()))
    if price > upper_sp:
        return context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'Sell baby!'), \
            context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'{symbol} @${price} overtakes {upper_sp} UPPER stop-price.')
    if price < lower_sp:
        return context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'Sell baby!'), \
            context.bot.send_message(chat_id=update.effective_chat.id, \
            text=f'{symbol} @${price} overtakes {lower_sp} LOWER stop-price.')
    time.sleep(2)
    return background_price_check(symbol, upper_sp, lower_sp, update, context)


### handler functions ###
# start
def start(update: Update, context: CallbackContext):
    content = update.to_dict()
    text_start1 = f'Hi {content["message"]["chat"]["first_name"]}! Welcome to Cryptocurrency Price Alert.\n'
    text_start2 = 'This bot sends you a notification if a cryptocurrency overtake stop-prices.\n\nHere the command list:\n'
    cm = '/start\n/setsymbol\n/setuppersp\n/setlowersp\n/startfollow\n/stopfollow\n/stop'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_start1+text_start2+cm)

# setsymbol
def set_symbol(update: Update, context: CallbackContext):
    symbol = ' '.join(context.args).upper() # TODO check if is a propper symbol
    with open('custom/currentCC', 'w') as f:
        f.write(f'{symbol}\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{symbol} symbol set.')

# setuppersp
def set_upper_sp(update: Update, context: CallbackContext):
    upper_sp = ' '.join(context.args) # TODO check if is a number
    with open('custom/currentCC', 'a') as f:
        f.write(f'{upper_sp}\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{upper_sp} $ upper stop price set.')

# setlowersp
def set_lower_sp(update: Update, context: CallbackContext):
    lower_sp = ' '.join(context.args) # TODO check if is a number
    with open('custom/currentCC', 'a') as f:
        f.write(f'{lower_sp}\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{lower_sp} $ lower stop price set.')

# startfollow
def start_follow(update: Update, context: CallbackContext):
    with open('custom/currentCC', 'r') as f:
        cc = f.read().splitlines()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Start following {cc[0]} with {cc[1]} - {cc[2]} $ bounds.')
    background_price_check(cc[0], float(cc[1]), float(cc[2]), update, context)

# TODO stopfollow

def unknown(update: Update, context: CallbackContext):
    incoming = update.to_dict()
    text_unk = f'Sorry {incoming["message"]["chat"]["first_name"]}, {incoming["message"]["text"]} command is unknown'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_unk)


# start
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# setsymbol
dispatcher.add_handler(CommandHandler('setsymbol', set_symbol))

# setuppersp
dispatcher.add_handler(CommandHandler('setuppersp', set_upper_sp))

# setlowersp
dispatcher.add_handler(CommandHandler('setlowersp', set_lower_sp))

# startfollow
dispatcher.add_handler(CommandHandler('startfollow', start_follow))

# unknown command
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


# bot run
updater.start_polling()
updater.idle()
updater.stop()
