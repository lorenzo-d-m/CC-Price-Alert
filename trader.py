import time


class Trader():
    def __init__(self, data_source: object, max_oldness_price=None):
        self.data_source = data_source
        self.max_oldness_price = max_oldness_price # max allowed oldness for price from data_souce
            

    def check_price_in_range(self, token_id, lower_sp, upper_sp) -> tuple:
            """
            It checks if the price of the token id is into the range
            Return code:
            ( price_if_under_lower_sp  ,        None         ,          None           ) or
            (        None              ,  price_if_in_range  ,          None           ) or
            (        None              ,        None         , price_if_above_upper_sp )
            """
            try:
                quotation = self.data_source.get_simple_price(token_id)
                if self.max_oldness_price:
                    if quotation[token_id]['last_updated_at'] < int( time.time() ) - self.max_oldness_price:
                        raise Exception(f'{token_id} price is more than {self.max_oldness_price} seconds old.')
            except Exception as e:
                raise Exception(e)
            else:
                price = quotation[token_id]['usd']
                if price < lower_sp:
                    return price, None, None
                elif price > upper_sp:
                    return None, None, price
                else:
                    return None, price, None
