from trading_bot import TradingBot
from backtest import backtest
from sklearn.ensemble import GradientBoostingRegressor
from testing import *

def run_backtest():
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    REG = GradientBoostingRegressor(random_state=0)
    tb = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1, CUTOFF_UPPER=100, \
                    SLPERC=0.05, TPPERC=0.05, \
                    NP_CUTOFF_PCT=0.8, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    df_btc_name, df_btc_backtest = tb.initialize_window_signaler_for_backtesting()
    results = backtest(tb, [df_btc_backtest], [df_btc_name], 'data_forex')
    tb.save_model(results)
    return results


from sklearn.ensemble import GradientBoostingRegressor
from serve import perform_routine
from trading_bot import TradingBot
from trade_handler import TradeHandler


if __name__ == "__main__":
    csv_path = 'csvs/updating_btc.csv'
    cached_prices_path = 'cached_prices.txt'
    
    REG = GradientBoostingRegressor(random_state=0)
    model = TradingBot(df_name=csv_path, \
                       REG=REG, \
                       CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                       SLPERC=0.05, TPPERC=0.05, \
                       NP_CUTOFF_PCT=0.95, \
                       shorts=False, \
                       window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    trade_handler = TradeHandler(model=model, \
                                 cash=100.0, \
                                 margin=1.0, \
                                 trade_size=1.0)
    perform_routine(csv_path, cached_prices_path, trade_handler)



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
    