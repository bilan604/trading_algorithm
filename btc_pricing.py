import re
import json
import requests
from datetime import datetime


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

