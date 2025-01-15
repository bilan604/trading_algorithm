import time
import json
import pandas as pd
from datetime import datetime, timezone
from helpers import get_btc_usd_price
from trade_handler import TradeHandler
from helpers import VM_log, update_origin


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
    # this should only be true on start. Whenever cached_prices.txt is cleared during runtime on a new day,
    # it gets a row added right afterwards
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
        
        VM_log(f"--->Current time was not a new day from cached_prices, or, cached_prices was empty.\n")
        VM_log(f"--->adding entry to cached prices - price: {str(price)}, time: {str(time)}\n")
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
    
    if data['High'][0] == None or data['Low'] == None:
        raise Exception("Attempted to add High: [None] and Low: [None] to bitcoin csv. cached_prices.txt was likely empty.")
    
    concat_data_to_dataframe(csv_path, data)

    # clear cache
    with open(cached_prices_path, "w+") as f:
        pass

    # add first of the day (open) to cache
    price, time = get_btc_usd_price()
    append_to_cached_prices(cached_prices_path, price, time)

    VM_log(f"--->Current time is a new day from times that were in cached_prices.txt. Cached has been cleared.\n")
    dff = pd.read_csv(csv_path)
    last_date = dff['Gmt time'].iloc[len(dff)-1]
    total_obj = str(len(dff))
    VM_log(f"--->There are now {total_obj} entries in {csv_path}. The last date in {csv_path} is {last_date}.\n")

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
    prev_time = None
    
    while True:
        curr_time = datetime.now(timezone.utc)

        should_perform = False
        if prev_time == None:
            should_perform = True
        if should_perform == False:    
            seconds_elapsed = get_seconds_difference(curr_time, prev_time)
            if seconds_elapsed >= 180:
                should_perform = True
        
        if should_perform:
            # logging
            VM_log(f"--->Performing routine event at {str(curr_time)}.\n")
            # the routine event is adding the btc price to the prices seen so far today
            perform_routine_event(trade_handler, csv_path, cached_prices_path)
            prev_time = curr_time
            if prev_time == None:
                raise Exception("perform_routine_event's prev_time is None. Will cause infinite loop. How.")
            
            VM_log(f"--->Updating origin after performing routine event at {str(datetime.now(timezone.utc))}.\n")
            
            update_origin()
        
        else:

            print("sleeping for 60 seconds")
            time.sleep(60)

