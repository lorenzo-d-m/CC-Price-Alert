import requests


class CoinGeckoDataSource:
    def __init__(self):
        self.coingecko_base_path = 'https://api.coingecko.com/api/v3/'
        self.geckoterminal_base_path = 'https://api.geckoterminal.com/api/v2/'

        # if MAX_OLDNESS_PRICE:
        #     self.max_oldness_price = MAX_OLDNESS_PRICE
        # else:
        #     self.max_oldness_price = None


    def get_simple_price(self, asset_id: str) -> dict:
        """
        HTTP request to CoinGecko API for the price of an asset.
        """
        try:
            response = requests.get(
                f'{self.coingecko_base_path}simple/price?ids={asset_id}&vs_currencies=usd&include_last_updated_at=true&precision=full'
                )
            
            # if self.max_oldness_price:
            #         if quotation[asset_id]['last_updated_at'] < int( time.time() ) - self.max_oldness_price:
            #             raise Exception(f'{asset_id} price is more than {self.max_oldness_price} seconds old.')
        except Exception as e:
            raise Exception(e)
        else:
            if response.status_code != 200:
                raise Exception("HTTP Response Error")
            if response.json() == {}:
                raise Exception("No price in HTTP Response")
            return response.json()
        

    def get_dex_price(self, network: str, contract: str, token: str = 'base') -> float:
        """
        HTTP request to GeckoTerminal API for the price of an asset.
        """
        try:
            response = requests.get(
                f'{self.geckoterminal_base_path}networks/{network}/pools/{contract}'
                )
        except Exception as e:
            raise Exception(e)
        else:
            if response.status_code != 200:
                raise Exception("HTTP Response Error")
            if response.json() == {}:
                raise Exception("No price in HTTP Response")
            return float(response.json().get('data').get('attributes').get(f'{token}_token_price_usd'))
        
    
    def get_historical_prices(self, asset_id: str, days_ago: int) -> tuple:
        """
        Data granularity is automatic (cannot be adjusted):
        1 day from current time = 5 minute interval data |
        1 - 90 days from current time = hourly data |
        above 90 days from current time = daily data (00:00 UTC)
        """
        response = requests.get(
            f'{self.coingecko_base_path}coins/{asset_id}/market_chart?vs_currency=usd&days={days_ago}'
            )
            
        if response.status_code != 200:
            raise Exception("HTTP Response Error")
        if response.json() == {}:
            raise Exception("No price in HTTP Response")
        
        price_time_list = response.json().get('prices')
        
        return tuple( (item[1] for item in price_time_list) )



# source = CoinGeckoDataSource()
# prices = source.get_historical_prices('ethereum', 2)
# price = source.get_simple_price('optimism')
# print(type(price), price)
