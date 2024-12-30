from trading_bot import TradingBot
from backtest import backtest
from sklearn.ensemble import GradientBoostingRegressor

def run_backtest():
    df_btc_name = 'btc_data_aggregated.csv'
    REG = GradientBoostingRegressor(random_state=0)
    tb = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1, CUTOFF_UPPER=100, \
                    SLPERC=0.02, TPPERC=0.02, \
                    NP_CUTOFF_PCT=0.8, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    df_btc_name, df_btc_backtest = tb.initialize_window_signaler_for_backtesting()
    results = backtest(tb, [df_btc_backtest], [df_btc_name], 'data_forex')
    tb.save_model(results)
    return results


results = run_backtest()
print("\n--------------------->results:")
print(results)
