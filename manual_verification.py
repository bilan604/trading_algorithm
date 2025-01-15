# USED FOR DEBUGGING

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

    # New method calls for additional functions
    generate_client_order_id = th.generate_client_order_id()
    print("\n-------------------->")
    print("generate_client_order_id:", generate_client_order_id)

    get_orders = th.get_orders()
    print("\n-------------------->")
    print("get_orders:", get_orders)

    get_open_orders = th.get_open_orders()
    print("\n-------------------->")
    print("get_open_orders:", get_open_orders)

    get_portfolio_uuid = th.get_portfolio_uuid()
    print("\n-------------------->")
    print("get_portfolio_uuid:", get_portfolio_uuid)

    get_portfolio_spot_positions = th.get_portfolio_spot_positions(get_portfolio_uuid)
    print("\n-------------------->")
    print("get_portfolio_spot_positions:", get_portfolio_spot_positions)

    get_crypto_value_of_asset_btc = th.get_crypto_value_of_asset("BTC")
    print("\n-------------------->")
    print("get_crypto_value_of_asset_btc:", get_crypto_value_of_asset_btc)

    get_product_price_btc_usdc = th.get_product_price("BTC-USDC")
    print("\n-------------------->")
    print("get_product_price_btc_usdc:", get_product_price_btc_usdc)

    get_btc_price = th.get_btc_price()
    print("\n-------------------->")
    print("get_btc_price:", get_btc_price)

    calculate_cash = th.calculate_cash()
    print("\n-------------------->")
    print("calculate_cash:", calculate_cash)

    get_all_buy_orders = th.get_all_buy_orders()
    print("\n-------------------->")
    print("get_all_buy_orders:", get_all_buy_orders)

    get_all_sell_orders = th.get_all_sell_orders()
    print("\n-------------------->")
    print("get_all_sell_orders:", get_all_sell_orders)

    check_existing_open_buy_order = th.check_existing_open_buy_order()
    print("\n-------------------->")
    print("check_existing_open_buy_order:", check_existing_open_buy_order)

    check_should_cancel_open_buy_order = th.check_should_cancel_open_buy_order()
    print("\n-------------------->")
    print("check_should_cancel_open_buy_order:", check_should_cancel_open_buy_order)

    check_exists_multiple_open_buy_orders = th.check_exists_multiple_open_buy_orders()
    print("\n-------------------->")
    print("check_exists_multiple_open_buy_orders:", check_exists_multiple_open_buy_orders)

    check_valid_open_sell_orders = th.check_valid_open_sell_orders()
    print("\n-------------------->")
    print("check_valid_open_sell_orders:", check_valid_open_sell_orders)

    get_latest_closed_buy_order = th.get_latest_closed_buy_order()
    print("\n-------------------->")
    print("get_latest_closed_buy_order:", get_latest_closed_buy_order)

    get_open_sell_order_for_current_position = th.get_open_sell_order_for_current_position()
    print("\n-------------------->")
    print("get_open_sell_order_for_current_position:", get_open_sell_order_for_current_position)

    load_current_position = th.load_current_position()
    print("\n-------------------->")
    print("load_current_position:", load_current_position)

    # Unused method calls
    #log_order
    #buy_bitcoin
    #place_sl_tp_sell_order
    #handle_trade
    #handle_new_day


api_key = get_env()["CDP_API_KEY"]
api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]
client = RESTClient(api_key=api_key, api_secret=api_secret)

#### uncomment this if th is initialized with self.model = tb instead of None
from trading_bot import TradingBot
from sklearn.ensemble import GradientBoostingRegressor
# TODO: tb is loading really fast. Check is it loading pretrained model?
REG = GradientBoostingRegressor(random_state=0)
tb = TradingBot('csvs/updating_btc.csv', REG, CUTOFF_LOWER=1, CUTOFF_UPPER=100, \
                SLPERC=0.05, TPPERC=0.05, \
                NP_CUTOFF_PCT=0.8, shorts=False, \
                window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
####

th = TradeHandler(tb, client, 1.0, 0.8)
generic_check(th)




print("DONE")
