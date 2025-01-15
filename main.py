from testing import *


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


<<<<<<< HEAD
if __name__ == '__main__':
    # using the backtest library, comparison of my trading algorithm v.s. michael harris trading method
    results = run_backtest()
    # compares XGBot against highest returning bot of 1000 randomly trading bots
    multitest()
    # simulates trading with Michael Harris indicator
    simulate_michael_harris()
    # compares XGBot against randomly trading bot
    simulate_both()
    # min, max, and average stats of 35 XGBots on different train/test split sizes
    view_spread()
    
=======
# Version of main for running main.py to test
if __name__ == '__main__':
    from testing import *
    # using the backtest library, comparison of my trading algorithm v.s. michael harris trading method
    results = run_backtest()
    # compares XGBot against highest returning bot of 1000 randomly trading bots
    #multitest()
    # simulates trading with Michael Harris indicator
    #simulate_michael_harris()
    # compares XGBot against randomly trading bot
    #simulate_both()
    # min, max, and average stats of 35 XGBots on different train/test split sizes
    #view_spread()

"""
# version of main for running the bot to trade BTC on Coinbase
if __name__ == "__main__":
    csv_path = 'csvs/updating_btc.csv'
    cached_prices_path = 'cached_prices.txt'
    REG = GradientBoostingRegressor(random_state=0)
    model = TradingBot(df_name=csv_path, \
                       REG=REG, \
                       CUTOFF_LOWER=0.7, CUTOFF_UPPER=100, \
                       SLPERC=0.04, TPPERC=0.04, \
                       NP_CUTOFF_PCT=0.90, \
                       shorts=False, \
                       window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    
    api_key = get_env()["CDP_API_KEY"]
    api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]
    client = RESTClient(api_key=api_key, api_secret=api_secret)
    
    trade_handler = TradeHandler(model=model, \
                                    client=client, \
                                    margin=1.0, \
                                    trade_size=0.1)
    
    ####
    # run tests by commenting out perform_routine() and adding code here
    #trade_handler.handle_new_day()
    ####
    perform_routine(csv_path, cached_prices_path, trade_handler)
"""
>>>>>>> ba5a4409ad2bfcd72e3daceec159b5ea2b1f99a7
