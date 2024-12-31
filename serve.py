import time
import json
import pandas as pd
from datetime import datetime, timezone
from btc_pricing import get_btc_usd_price
from trade_handler import TradeHandler


def get_seconds_difference(dt1, dt2):
    datediff = dt1 - dt2
    return datediff.seconds

def append_to_cached_prices(path, price, time):
    obj = {
        'price': price,
        'updatedISO': time
    }
    obj = json.dumps(obj)
    with open(path, 'a') as f:
        f.write(obj + '\n')

def load_cached_prices(path):
    objs = []
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            objs.append(obj)
    return objs

def is_new_day_from_cached_prices(path):
    dt1 = datetime.now(timezone.utc)
    cached_prices = load_cached_prices(path)
    if not cached_prices:
        return False
    first_price = datetime.fromisoformat(cached_prices[0]['updatedISO'])
    if (dt1.year, dt1.month, dt1.day) == (first_price.year, first_price.month, first_price.day):
        return False
    return True

def update_btc_csv(csv_path, cached_prices_path):

    def gmt_time_from_cached_price(obj):
        dt = datetime.fromisoformat(obj['updatedISO'])
        return f'{str(dt.year)}-{str(dt.month)}-{str(dt.day)} 00:00:00'
    
    def concat_data_to_dataframe(path, data):
        df = pd.read_csv(path)
        df_new = pd.DataFrame(data)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_csv(path, index=False)

    should_update = is_new_day_from_cached_prices(cached_prices_path)
    if not should_update:
        price, time = get_btc_usd_price()
        append_to_cached_prices(cached_prices_path, price, time)
        return False
    
    # add cache to csv
    cache = load_cached_prices(cached_prices_path) 
    # cache should never be empty here as should_update is false for empty cache
    Gmt_time = gmt_time_from_cached_price(cache[0])
    data = {
        'Gmt time': [Gmt_time],
        'Open': [float(cache[0]['price'])],
        'High': [None],
        'Low': [None],
        'Close': [float(cache[-1]['price'])]
    }
    for obj in cache:
        curr_price = float(obj['price'])
        if (data['High'][0] == None) or data['High'][0] <= curr_price:
            data['High'][0] = curr_price
        if (data['Low'][0] == None) or data['Low'][0] >= curr_price:
            data['Low'][0] = curr_price
    
    concat_data_to_dataframe(csv_path, data)

    # clear cache
    with open(cached_prices_path, "w+") as f:
        pass

    # add first of the day (open) to cache
    price, time = get_btc_usd_price()
    append_to_cached_prices(cached_prices_path, price, time)

    return True

def perform_routine_event(trade_handler, csv_path, cached_prices_path):
    updated = update_btc_csv(csv_path, cached_prices_path)
    if updated == True:
        # handle trading logic
        trade_handler.handle_new_day()
    return

def perform_routine(csv_path, cached_prices_path, trade_handler):
    # (a routine consists of routine events) - every hour this function calls the update event
    print("\n----------------------> perform_routine() initial call!")
    prev_time = datetime.now(timezone.utc)
    
    while True:
        curr_time = datetime.now(timezone.utc)
        seconds_elapsed = get_seconds_difference(curr_time, prev_time)
        if seconds_elapsed <= 3600:
            print("sleeping for 600 seconds")
            time.sleep(600)
        else:
            perform_routine_event(trade_handler, csv_path, cached_prices_path)
            prev_time = curr_time


from sklearn.ensemble import GradientBoostingRegressor
from trading_bot import TradingBot
if __name__ == "__main__":
    csv_path = 'csvs/btc_data_aggregated.csv'
    cached_prices_path = 'cached_prices.txt'
    
    REG = GradientBoostingRegressor(random_state=0)
    model = TradingBot(df_name=csv_path, \
                       REG=REG, \
                       CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                       SLPERC=0.05, TPPERC=0.05, \
                       NP_CUTOFF_PCT=0.95, \
                       shorts=False, \
                       window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    trade_handler = TradeHandler(model=model, \
                                 cash=100.0, \
                                 margin=1.0, \
                                 trade_size=1.0)
    perform_routine(csv_path, cached_prices_path, trade_handler)
