import random
import pandas as pd

class Position(object):
    def __init__(self, entry_price, shares, date, slperc, tpperc, commision, short):
        self.entry_price = entry_price # price before commision
        self.shares = shares
        self.date = date
        self.slperc = slperc
        self.tpperc = tpperc
        self.commision = commision
        self.short = short


class ControlBot(object):
    def __init__(self, df_name, p = 0.01, SLPERC=0.04, TPPERC=0.04, shorts=False):
        self.name = "ControlBot"
        self.df_name = df_name
        self.df = pd.read_csv(self.df_name)
        self.p = p
        self.SLPERC = SLPERC
        self.TPPERC = TPPERC
        self.current_position = []
        self.shorts = shorts
    
    def btc_total_signal(self, X_test_index, is_global_index):
        if (random.randint(1, 100) / 100) <= self.p:
            return 2
        return 0


class MichaelHarris(object):
    def __init__(self, df_name, SLPERC=0.04, TPPERC=0.04, shorts=False):
        self.name = "MichaelHarrisBot"
        self.df_name = df_name
        self.df = pd.read_csv(self.df_name)
        self.SLPERC = SLPERC
        self.TPPERC = TPPERC
        self.current_position = []
        self.shorts = shorts
    
    def btc_total_signal(self, current_pos, is_global_index=True):
        df = self.df
        c1 = df['High'].iloc[current_pos] > df['High'].iloc[current_pos-1]
        c2 = df['High'].iloc[current_pos-1] > df['Low'].iloc[current_pos]
        c3 = df['Low'].iloc[current_pos] > df['High'].iloc[current_pos-2]
        c4 = df['High'].iloc[current_pos-2] > df['Low'].iloc[current_pos-1]
        c5 = df['Low'].iloc[current_pos-1] > df['High'].iloc[current_pos-3]
        c6 = df['High'].iloc[current_pos-3] > df['Low'].iloc[current_pos-2]
        c7 = df['Low'].iloc[current_pos-2] > df['Low'].iloc[current_pos-3]
        if c1 and c2 and c3 and c4 and c5 and c6 and c7:
            return 2
        return 0