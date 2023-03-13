import time
from data_sources import CoinGeckoDataSource


class Trader():
    asset_id = None
    lower_sp = None
    upper_sp = None
    entry_price = None
    local_th = None

    def __init__(self, max_oldness_price=None):
        self.data_source = CoinGeckoDataSource()
        self.max_oldness_price = max_oldness_price # max allowed oldness for price from data_souce


    def check_price_in_range(self) -> tuple:
            """
            It checks if the price of the asset id is into the range
            Return code:
            ( price_if_under_lower_sp  ,        None         ,          None           ) or
            (        None              ,  price_if_in_range  ,          None           ) or
            (        None              ,        None         , price_if_above_upper_sp )
            """
            try:
                quotation = self.data_source.get_simple_price(self.asset_id)
                if self.max_oldness_price:
                    if quotation[self.asset_id]['last_updated_at'] < int( time.time() ) - self.max_oldness_price:
                        raise Exception(f'{self.asset_id} price is more than {self.max_oldness_price} seconds old.')
            except Exception as e:
                raise Exception(e)
            else:
                price = quotation[self.asset_id]['usd']
                if price < self.lower_sp:
                    return price, None, None
                elif price > self.upper_sp:
                    return None, None, price
                else:
                    return None, price, None


    def trade_strategy(self):
        self.entry_price