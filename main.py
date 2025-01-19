from coinbase.rest import RESTClient
from sklearn.ensemble import GradientBoostingRegressor

from trading_bot import TradingBot
from trade_handler import TradeHandler

from serve import perform_routine
from helpers import get_env, clear_caches


# version of main for running the bot to trade BTC on Coinbase
if __name__ == "__main__":
    # clear VM_log and cached_prices text files
    clear_caches()

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
                                    trade_size=0.4)
    
    perform_routine(csv_path, cached_prices_path, trade_handler)
