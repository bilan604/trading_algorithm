
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

def generate_client_order_id():
    import random
    new_order_id = ""
    for i in range(15):
        new_order_id += str(random.randint(1, 9))
    return new_order_id


from coinbase.rest import RESTClient
from json import dumps


api_key = get_env()["CDP_API_KEY"]
api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]

client = RESTClient(api_key=api_key, api_secret=api_secret)

accounts = client.get_accounts()
print(accounts.to_dict())
for account in accounts.to_dict()['accounts']:
    print("\n------------>account:")
    print(account)
#32Rov2L8hmWi1smcsaUnqPuoTzP232Z6YD

# account = accounts.to_dict()['accounts'][0]
# 04463caf-31aa-5f88-be57-a1956be86e44
# 379d9e84-17ac-5b16-8fb6-c7fec0948c25 # has btc
print("uuid:", account['uuid'])





import math

product = client.get_product("ETH-BTC")
btc_usd_price = float(product["price"])
adjusted_btc_usd_price = str(math.floor(btc_usd_price - (btc_usd_price * 0.05)))






"""
if False:
    new_order_id = generate_client_order_id()
    order = client.market_order_buy(
        client_order_id=new_order_id,
        product_id="ETH-BTC",
        quote_size="0.00001"
    )

    if order['success']:
        order_id = order['success_response']['order_id']
        fills = client.get_fills(order_id=order_id)
        print(dumps(fills.to_dict()))
"""




print("Finished Execution in coinbase_handler.py")

