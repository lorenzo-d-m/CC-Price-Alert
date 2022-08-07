"""
Author: Lorenzo
Date: 31/07/2022

Cryptocurrency data handling based on CoinMarketCap free API
"""

def get_price(symbol):
    from requests import Request, Session
    from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
    from custom.api_keys import COINMARKETCAP_API_KEY
    import json


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


    # map symbols : ids
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
                return price
                # break
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        return None
