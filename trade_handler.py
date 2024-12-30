
from trading_bot import TradingBot


class Position(object):
    def __init__(self, entry_price, shares, date, slperc, tpperc, commision, short):
        self.entry_price = entry_price # price before commision
        self.shares = shares
        self.date = date
        self.slperc = slperc
        self.tpperc = tpperc
        self.commision = commision
        self.short = short


class TradeHandler:

    def __init__(self, model, cash, margin, trade_size):
        self.model = model # the trading bot
        self.cash = cash # the total amount to cash it is allowed to use
        self.margin = margin # leverage
        self.trade_size = trade_size # the maximum proportion of the cash the bot is allowed to use in one trade

        self.current_position = [] # to override the model's current position
        self.acceptable_commision_rate = 0.01 # what range of yesterday's close


    def buy_bitcoin(self):
        # implement with tests first
        pass

    def sell_bitcoin(self):
        # implement with tests first
        pass

    def handle_new_day(self):
        # this function triggers when a new day has arrived
        # and the btc csv has been updated with yesterday's information
        print("TradeHandler.handle_new_day() called")

        self.model.initialize_window_signaler()
        self.model.train_model()

        idx_yesterday = len(self.model.df) - 1
        Xi = self.model.X[idx_yesterday:idx_yesterday+1] # moving averages and input for yesterday
        date = self.model.df['Gmt time'][idx_yesterday] # yesterday
        print("Predicting for date", date)

        # signal: 0 for pass, 1 for short, 2 for buy
        signal = self.model.btc_total_signal(idx_yesterday, is_global_index=True)

        # consider future selling if is good time to short, problem is no idea where the cutoffs should be yet

        if signal == 0:
            pass
        if signal == 1:
            pass
        if signal == 2:
            self.buy_bitcoin()









