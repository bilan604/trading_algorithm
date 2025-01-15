import re
import json
import requests
from datetime import datetime


def VM_log(s, file_path='VM_logs.txt'):
    with open(file_path, 'a') as f:
        if s and s[-1] != "\n":
            s += "\n"
        f.write(s)


def get_env(path=".env"):
    env = {}
    with open(path, "r") as f:
        for line in f.readlines():
            if not line.strip():
                continue
            if line[0] == "#":
                continue
            items = line[:-1].split("=")
            name = items[0]
            value = "=".join(items[1:])
            env[name] = value
    return env

def clear_caches():
    with open('VM_logs.txt', 'w+') as f:
        pass
    with open('cached_prices.txt', 'w+') as f:
        pass

def format_price_time(price, time):
    # time is 5 hours ahead, UTC time
    price = re.sub(",", "", price)
    time = datetime.fromisoformat(time).isoformat()
    return price, time

def get_btc_usd_price():
    # time is 5 hours ahead, UTC time
    url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
    resp = requests.get(url)
    obj = json.loads(resp.text)

    btc_price = obj['bpi']['USD']['rate']
    time = obj['time']['updatedISO']
    price, time = format_price_time(btc_price, time)
    return price, time