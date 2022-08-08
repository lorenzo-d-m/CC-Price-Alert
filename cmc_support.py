"""
Author: Lorenzo
Date: 31/07/2022

Cryptocurrency data handling based on CoinMarketCap free API
"""

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from custom.api_keys import COINMARKETCAP_API_KEY
import json
import time

def get_price(symbol):
    #set API
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    session = Session()
    session.headers.update(headers)
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    params =  {
        'start':'1',
        'limit':'200',
    }


    # symbols : ids mapping
    mapping = {
        'BTC': 1,
        'ETH': 1027,
        'SOL': 5426,
    }


    if symbol not in mapping.keys(): # check data from bot
        return 'Symbol not supported or not properly written!'


    price = 0 # initialization
    try:
        response = session.get(url, params=params)
        data = json.loads(response.text)
        for currency in data['data']:
            if currency['id'] == mapping[symbol]:
                price = float(currency['quote']['USD']['price'])
                last_updated = currency['last_updated']
                return price, last_updated
    except (ConnectionError, Timeout, TooManyRedirects, Exception) as e:
        print('Coin Market Cap API error:', e)
        raise Exception('Error')


# def get_priceTest(symbol):
#     import random
#     return random.gauss(10, 0.8), 'now'


def background_price_check(symbol, upper_sp, lower_sp, update, context, stop_event):
    try: # get real time price
        price, last_updated = get_price(symbol)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Error gathering real-time {symbol} price')
    else:
        print(f'{symbol} @${price}. Upper sp: ${upper_sp}, Lower sp: ${lower_sp} - Last updated: {last_updated}')
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

        for i in range(10):
            if stop_event.is_set():
                return context.bot.send_message(chat_id=update.effective_chat.id, text=f'Stop following {symbol}')
            time.sleep(1)
        return background_price_check(symbol, upper_sp, lower_sp, update, context, stop_event)