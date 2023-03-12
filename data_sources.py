import requests


class CoinGeckoDataSource:
    def __init__(self):
        self.base_path = 'https://api.coingecko.com/api/v3/'
        self.max_delta_time = 5 * 60
        
    def get_simple_price(self, token_id: str) -> dict:
        """
        It requests to the HTTP CoinGecko API the price of a token id.
        """
        try:
            response = requests.get(
                f'{self.base_path}simple/price?ids={token_id}&vs_currencies=usd&include_last_updated_at=true&precision=full'
                )
        except Exception as e:
            raise Exception(e)
        else:
            if response.status_code != 200:
                raise Exception("HTTP Response Error")
            if response.json() == {}:
                raise Exception("No price in HTTP Response")
        
        data = response.json()
        return data
