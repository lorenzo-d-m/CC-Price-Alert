from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    ConversationHandler, 
    ApplicationBuilder, 
    filters
)
import logging
from custom.api_keys import TELEGRAM_BOT_API_KEY
from callback_functions import *


# https://github.com/python-telegram-bot/python-telegram-bot/wiki


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    
def handler():
    """
    Application (bot) handler.
    It listens for user commands or messages and calls relative callback functions.
    """
    # application instance
    application = ApplicationBuilder().token(TELEGRAM_BOT_API_KEY).concurrent_updates(True).build()
    
    
    # /start command
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)


    # /setassetrange command
    asset_range_conversation_handler = ConversationHandler(
        entry_points = [CommandHandler("setassetrange", asset_range)],
        states={
            TO_SET_ASSET: [
                MessageHandler(filters.TEXT, set_asset_get_lowersp),
            ],
            TO_SET_LOWER_SP: [
                MessageHandler(filters.Regex('(\d*\.)?\d+') , set_lowersp_get_uppersp),
            ],
            TO_SET_UPPER_SP: [
                MessageHandler(filters.Regex('(\d*\.)?\d+') , set_uppersp),
            ]
        },
        fallbacks=[
            CommandHandler('clean', clean_asset_range),
            CommandHandler('startfollow', start_follow_asset_range)
        ],
    )
    application.add_handler(asset_range_conversation_handler)


    # /stopassetrange command
    stop_asset_range_handler = CommandHandler('stopassetrange', stop_follow_asset_range)
    application.add_handler(stop_asset_range_handler)


    # /getactivear command
    get_active_tr_handler = CommandHandler('getactivear', get_active_asset_range)
    application.add_handler(get_active_tr_handler)    
    

    # run Telegram bot
    application.run_polling()


# bot entry point
if __name__ == '__main__':
    handler()