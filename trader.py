import time
from data_sources import CoinGeckoDataSource


class Trader():
    asset_id = None
    lower_sp = None
    upper_sp = None

    network = 'optimism'
    contract = '0x1c3140ab59d6caf9fa7459c6f83d4b52ba881d36'
    entry_price = None # float
    local_max = 0 # float
    local_min = 0 # float
    ref_1 = None # ref_1 is one step before ref_0
    ref_0 = None # ref_0 is one step after ref_1

    def __init__(self, max_oldness_price=None):
        self.data_source = CoinGeckoDataSource()
        self.max_oldness_price = max_oldness_price # max allowed oldness for price from data_souce

    def get_avg_std(self, days: int) -> dict:
        """
        It return: price, max, min, avg, std, and volatility.
        """
        from math import sqrt

        prices = self.data_source.get_historical_prices(self.asset_id, days)
        avg = sum(prices) / len(prices)
        std = sqrt( ( sum([p**2 for p in prices]) / len(prices) ) - ( avg ** 2 ) )
        volatility = std / avg * 100

        quotation = self.data_source.get_simple_price(self.asset_id)
        price = quotation[self.asset_id]["usd"]
        t = time.localtime( quotation[self.asset_id]["last_updated_at"] ) # (tm_year=2023, tm_mon=3, tm_mday=22, tm_hour=21, tm_min=56, tm_sec=23, tm_wday=2, tm_yday=81, tm_isdst=0)

        return {
            "price": f'$ {price} {t[0]}-{t[1]}-{t[2]} {t[3]}:{t[4]}',
            "max": max(prices),
            "min": min(prices),
            "avg": avg,
            "volatility": f'\u00B1 {volatility:.1f}%'
        }


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


    def check_to_sell(self, price) -> bool:
        # maximum allowed loss
        max_loss = 0.97 # -3%
        max_loss_below_local_max = 0.97 # -3%
        
        # get price from DEX
        # price = self.data_source.get_dex_price(self.network, self.contract)

        # check maximum allowed loss
        if price < self.entry_price * max_loss:
            return  True

        # references initialization
        if not self.ref_1:
            self.ref_1 = price
            
        if self.ref_1 and ( not self.ref_0 ):
            self.ref_0 = price

        # trend monitoring
        if self.ref_1 > self.ref_0 < price:
            self.local_min = self.ref_0

        if self.ref_1 > self.ref_0 > price:
            pass

        if self.ref_1 < self.ref_0 < price:
            pass

        if self.ref_1 < self.ref_0 > price:
            self.local_max = self.ref_0
            
        # check loss from local max
        if price < self.local_max * max_loss_below_local_max:
            return True

       
        # ref step ahead
        self.ref_1 = self.ref_0
        self.ref_0 = price
        return False
    

    def stop_prices_strategy(self, price):
        """
        Random buy and stop-prices-based sell. It returns true if you have to sell, false otherwise
        """
        if price < self.entry_price * 0.91:
            return True
        if price > self.entry_price * 1.03:
            return True
        return False


if __name__ == '__main__':
    import random
    # prices = []
    # for i in range(50):
    #     p = random.gauss(1645, 95.5)
    #     if p > 0 :
    #         prices.append( p )

    data_source = CoinGeckoDataSource()
    prices = data_source.get_historical_prices('ethereum', 60)

    capital = 100
    runs = 10 ** 3
    slipage_perc = 0.1 # 0.1%
    avg_runs = 0
    for _ in range(runs): # montecarlo iterations
        entry_idx = random.randint( 0, int( len(prices)*0.8 ) )
        entry_price = prices[entry_idx]
        capital = ( capital * (1 - slipage_perc/100) ) - 0.25
        for price in prices[entry_idx + 1:]:
            if price < entry_price: # sell
                capital = ( capital * (1 - slipage_perc/100) ) - 0.25
                break
        capital = capital * (price / entry_price)
    print(capital)


       
    

    # capital = 100
    # runs = 100
    # avg_runs = 0
    # for _ in range(runs):
    #     entry_idx = random.randint( 0, int( len(prices)*0.8 ) )
    #     tr.entry_price = prices[entry_idx]
    #     capital = capital - 0.5

    #     for i, price in enumerate( prices[entry_idx+1:], start=1):
    #         if tr.stop_prices_strategy(price):
    #             capital = (capital * price / tr.entry_price) - 0.5
    #             print(tr.entry_price, price)
    #             break
    #     avg_runs += i/runs
    # print('Capital:', capital)
    # print('Avg runs:', avg_runs)
