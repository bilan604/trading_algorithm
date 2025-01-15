# For Coinbase authorization of IPs
import requests
from bs4 import BeautifulSoup


def get_IP():
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


print(get_IP())


