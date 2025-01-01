from trade_handler import TradeHandler


from coinbase.rest import RESTClient
from json import dumps


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


def generic_check(th):
    orders = th.get_orders()
    uuid = th.get_portfolio_uuid()
    spot_positions = th.get_portfolio_spot_positions(uuid)
    new_order_id = th.generate_client_order_id()
    btc_available_in_usd = th.get_fiat_value_of_asset("BTC")
    btc_available = th.get_crypto_value_of_asset("BTC")
    usdc_available_in_usd = th.get_fiat_value_of_asset("USDC")
    usdc_available = th.get_crypto_value_of_asset("USDC")
    #log_order
    btc_usdc_price = th.get_product_price("BTC-USDC")
    btc_price = th.get_btc_price()
    #buy_bitcoin
    #place_sl_tp_sell_order
    cash = th.calculate_cash()
    #handle_trade
    #handle_new_day
    
    print("orders:", orders)
    print("uuid:", uuid)
    print("spot_positions:", spot_positions)
    print("new_order_id:", new_order_id)
    print("btc_available:", btc_available)
    print("new_order_id:", new_order_id)  # Prints the newly generated order ID
    print("btc_available_in_usd:", btc_available_in_usd)  # Available BTC balance in USD
    print("btc_available:", btc_available)  # Available BTC balance in crypto
    print("usdc_available_in_usd:", usdc_available_in_usd)  # Available USDC balance in USD
    print("usdc_available:", usdc_available)  # Available USDC balance in crypto
    print("btc_usdc_price:", btc_usdc_price)  # BTC price in USDC from get_product_price
    print("btc_price:", btc_price)  # BTC price from get_btc_price
    print("cash (USDC):", cash)  # Cash available (USDC)
    



def check_should_cancel_buy_position(self):
    # TODO: put this in th
    # TODO: add cancelling buy position
    # also, why would a market order buy not go through?
    # and if it cancels a buy, wouldn't that open up risk to rebuying, etc?
    from datetime import datetime, timezone
    dt1 = datetime.now(timezone.utc)
    dt2 = datetime.fromisoformat('2025-01-01T20:20:12.619384Z')
    diff = dt1 - dt2
    hours_elapsed = (diff.days * 24) + (diff.seconds // 3600)
    if hours_elapsed >= 24:
        #cancel buy position
        pass

