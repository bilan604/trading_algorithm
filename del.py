# USED FOR TESTING ISOLATED CODE DURING DEVELOPMENT


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

from trade_handler import TradeHandler

from coinbase.rest import RESTClient
from json import dumps


api_key = get_env()["CDP_API_KEY"]
api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]

client = RESTClient(api_key=api_key, api_secret=api_secret)
th = TradeHandler(None, client, 1.0, 0.8)

def get_orders(self):
    orders = self.client.list_orders()
    orders = orders.to_dict()
    print(orders['orders'])    
    return orders

def get_portfolio_uuid(self):
    portfolios = self.client.get_portfolios()
    portfolios = portfolios.to_dict()
    for portfolio in portfolios['portfolios']:
        if portfolio['name'] == 'Default':
            return portfolio['uuid']
    return None

def get_portfolio_spot_positions(self, uuid):
    portfolio = client.get_portfolio_breakdown('25b79e39-3cd0-5a5e-8a60-6a06ded7f747')
    portfolio = portfolio.to_dict()
    spot_positions = portfolio['breakdown']['spot_positions']
    print(spot_positions)
    return spot_positions

portfolio = client.get_portfolio_breakdown('25b79e39-3cd0-5a5e-8a60-6a06ded7f747')
portfolio = portfolio.to_dict()
spot_positions = portfolio['breakdown']['spot_positions']
for spot_position in spot_positions:
    print("\n-------->")
    print(spot_position)
    # eth: 0.00027702

# listing orders
orders = th.client.list_orders()
orders = orders.to_dict() # reverse order, index 0 is newer orders
for order in orders['orders']:
    print("\n----------->order:")
    order_id = order['order_id']
    order_side = order['side'] # 'BUY', 'SELL'
    order_status = order['status'] # 'FILLED'

####
from btc_pricing import get_btc_usd_price 
print("price 1:", get_btc_usd_price())

product = client.get_product("BTC-USDC")
btc_usdc_price = float(product["price"])
print("price 2:", btc_usdc_price)

available_btc = th.get_crypto_value_of_asset('BTC')
base_size = round(0.33 * available_btc, 8)
limit_price = round(btc_usdc_price * (1.0 + 0.02), 2)
stop_trigger_price = round(btc_usdc_price * (1.0 - 0.02), 2)

def code_example_market_sell_bitcoin_into_usdc(th):
    # tested, works
    new_order_id = th.generate_client_order_id()
    order = client.market_order_sell(
        client_order_id=new_order_id,
        product_id="BTC-USDC",
        base_size=str(base_size)
    )

    if order['success']:
        order_id = order['success_response']['order_id']
        fills = client.get_fills(order_id=order_id)
        dumps(fills.to_dict())
    else:
        error_response = order['error_response']
        print(error_response)

def code_example_trigger_bracket_order_gtc_sell(client, th):
    product = client.get_product("BTC-USDC")
    btc_usdc_price = float(product["price"])
    print("price 2:", btc_usdc_price)

    available_btc = th.get_crypto_value_of_asset('BTC')
    base_size = round(0.33 * available_btc, 8)
    limit_price = round(btc_usdc_price * (1.0 + 0.02), 2)
    stop_trigger_price = round(btc_usdc_price * (1.0 - 0.02), 2)


    # trigger_bracket_order_gtc_sell:
    # places a sell order that triggers at tp and sl
    new_order_id = th.generate_client_order_id()
    order = th.client.trigger_bracket_order_gtc_sell(
        client_order_id=new_order_id,
        product_id='BTC-USDC',
        base_size=str(base_size),
        limit_price=str(limit_price), # +4%
        stop_trigger_price=str(stop_trigger_price), #-4% 
    )

    if order['success']:
        order_id = order['success_response']['order_id']
        fills = client.get_fills(order_id=order_id)
        dumps(fills.to_dict())
    else:
        error_response = order['error_response']
        print(error_response)

"""
    
    
    # a sell limit order can only be executed at the limit price or HIGHER
    client.stop_limit_order_sell(
        client_order_id=,
        product_id=,
        base_size=,
        limit_price=,
        stop_price=,
        stop_direction=,
    )
"""



print("Finished")

