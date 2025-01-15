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

def get_IP():
    import requests
    from bs4 import BeautifulSoup

    url = 'https://whatismyv6.com/'

    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')

    tables = soup.find_all('table')
    table = None
    for tbl in list(tables):
        if 'You are connecting with an' in tbl.text:
            table = tbl
            break

    table_elements = table.text.strip().split("\n")    
    print(table_elements[0])
    IP = table_elements[1]
    return IP

def update_origin():
    import subprocess

    lines = [
        'git config --global user.email "bilan604@yahoo.com"',
        'git config --global user.name "bilan604"',
        'git config --global user.password "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"',
        'git add .',
        'git commit -m "auto"',
        'git push origin VM_trading'
    ]
    for line in lines:
        print("update_origin bash execution():")
        print('line:', line)
        output = subprocess.run(line.strip().split(" "), capture_output=True, text=True)
        print("output:", output.stdout)


