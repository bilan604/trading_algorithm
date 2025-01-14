
from sklearn.ensemble import GradientBoostingRegressor
from serve import perform_routine
from trading_bot import TradingBot
from trade_handler import TradeHandler

from coinbase.rest import RESTClient


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


# version of main for running the bot to trade BTC on Coinbase
if __name__ == "__main__":
    csv_path = 'csvs/updating_btc.csv'
    cached_prices_path = 'cached_prices.txt'
    REG = GradientBoostingRegressor(random_state=0)
    model = TradingBot(df_name=csv_path, \
                       REG=REG, \
                       CUTOFF_LOWER=0.7, CUTOFF_UPPER=100, \
                       SLPERC=0.05, TPPERC=0.05, \
                       NP_CUTOFF_PCT=0.90, \
                       shorts=False, \
                       window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    
    api_key = get_env()["CDP_API_KEY"]
    api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]
    client = RESTClient(api_key=api_key, api_secret=api_secret)
    
    trade_handler = TradeHandler(model=model, \
                                    client=client, \
                                    margin=1.0, \
                                    trade_size=0.45)
    
    perform_routine(csv_path, cached_prices_path, trade_handler)


# Version of main for running main.py to test
#if __name__ == '__main__':
    # using the backtest library, comparison of my trading algorithm v.s. michael harris trading method
    #results = run_backtest()
    # compares XGBot against highest returning bot of 1000 randomly trading bots
    #multitest()
    # simulates trading with Michael Harris indicator
    #simulate_michael_harris()
    # compares XGBot against randomly trading bot
    #simulate_both()
    # min, max, and average stats of 35 XGBots on different train/test split sizes
    #view_spread()
    