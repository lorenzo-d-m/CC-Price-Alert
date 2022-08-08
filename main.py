"""
Author: Lorenzo

Simple Telegram bot triggered by cryptocurrency stop-prices.
"""
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update
from telegram.ext import CallbackContext
import logging
import threading
import time
from custom.api_keys import TELEGRAM_BOT_API_KEY
from cmc_support import *


######################################################################################################
# Telegram bot flow:
# Updater (it listens for messages)--> queue (uncontrollable) --> Dispatcher (controlled by handler) #
######################################################################################################

# TODO check user id

bot = telegram.Bot(token=TELEGRAM_BOT_API_KEY)
print(bot.get_me())

updates = bot.get_updates()
print(updates)
#bot.send_message(text='Sell baby!', chat_id=622124736)

updater = Updater(token=TELEGRAM_BOT_API_KEY, use_context=True)
dispatcher = updater.dispatcher

# log
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


### handler functions ###
# start
def start(update: Update, context: CallbackContext):
    print('/start')
    content = update.to_dict()
    text_start1 = f'Hi {content["message"]["chat"]["first_name"]}! Welcome to Cryptocurrency Price Alert.\n'
    text_start2 = 'This bot sends you a notification if a cryptocurrency overtake stop-prices.\n\nHere the command list:\n'
    cm = '/start\n/setsymbol\n/setuppersp\n/setlowersp\n/startfollow\n/stopfollow\n/stop'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_start1+text_start2+cm)


# setsymbol
def set_symbol(update: Update, context: CallbackContext):
    print('/setsymbol')
    symbol = ' '.join(context.args).upper()
    with open('custom/currentCC', 'w') as f:
        f.write(f'{symbol}\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'{symbol} symbol set.')


# setuppersp
def set_upper_sp(update: Update, context: CallbackContext):
    print('/setuppersp')
    upper_sp = ' '.join(context.args)
    if upper_sp.replace('.', '', 1).isdigit():
        with open('custom/currentCC', 'a') as f:
            f.write(f'{upper_sp}\n')
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'{upper_sp} $ upper stop price set.')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'The upper stop-price must be a number. Retry.')


# setlowersp
def set_lower_sp(update: Update, context: CallbackContext):
    print('/setlowersp')
    lower_sp = ' '.join(context.args)
    if lower_sp.replace('.', '', 1).isdigit():
        with open('custom/currentCC', 'a') as f:
            f.write(f'{lower_sp}\n')
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'{lower_sp} $ lower stop price set.')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'The lower stop-price must be a number. Retry.')


# startfollow
def start_follow(update: Update, context: CallbackContext):
    print('/startfollow')
    with open('custom/currentCC', 'r') as f:
        cc = f.read().splitlines()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Start following {cc[0]} with {cc[1]} - {cc[2]} $ bounds.')
    
    # background live price checker
    stop_event.clear()
    func_args=(cc[0], float(cc[1]), float(cc[2]), update, context, stop_event)
    threading.Thread(target=background_price_check, name='background_price_check', args=func_args).start()


# stopfollow
def stop_follow(update: Update, context: CallbackContext):
    print('/stopfollow')
    stop_event.set()
    #context.bot.send_message(chat_id=update.effective_chat.id, text='Stoped')


# unknown
def unknown(update: Update, context: CallbackContext):
    print('/unknown')
    incoming = update.to_dict()
    text_unk = f'Sorry {incoming["message"]["chat"]["first_name"]}, {incoming["message"]["text"]} command is unknown'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_unk)


### Dispatcher ###
# start
dispatcher.add_handler(CommandHandler('start', start))

# setsymbol
dispatcher.add_handler(CommandHandler('setsymbol', set_symbol))

# setuppersp
dispatcher.add_handler(CommandHandler('setuppersp', set_upper_sp))

# setlowersp
dispatcher.add_handler(CommandHandler('setlowersp', set_lower_sp))

# startfollow
stop_event = threading.Event() # thread handler for background price check
dispatcher.add_handler(CommandHandler('startfollow', start_follow))

# stopfollow
dispatcher.add_handler(CommandHandler('stopfollow', stop_follow))

# unknown command
dispatcher.add_handler(MessageHandler(Filters.command, unknown))


# run Telegram bot
updater.start_polling()
updater.idle()
updater.stop()
