import os
import re
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime

import joblib



class TradingBot(object):
    def __init__(self, df_name, REG, \
                 CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                 SLPERC=0.04, TPPERC=0.06, \
                 NP_CUTOFF_PCT=0.8, \
                 window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960],
                 shorts=False):
        
        self.CUTOFF_LOWER = CUTOFF_LOWER
        self.CUTOFF_UPPER = CUTOFF_UPPER

        self.SLPERC = SLPERC
        self.TPPERC = TPPERC

        self.window_sizes = window_sizes

        self.df_name = df_name
        self.df = None

        self.NP_CUTOFF_PCT = NP_CUTOFF_PCT
        self.NP_CUTOFF_VALUE = None #int(self.NP_CUTOFF_PCT * len(df_btc))

        self.REG = REG
        self.loaded_pretrained_model = False

        self.X = None
        self.y = None

        self.X_train = None
        self.y_train = None

        self.X_test = None
        self.y_test = None

        self.MEAN = None
        self.STD_DEV = None

        self.shorts = shorts # whether it takes short positions

        self.initialize()

    def initialize(self):
        def convert_btc_df_dates_to_index(df):
            lst = list(df['Gmt time'])
            df['Gmt time'] = [time.split(' ')[0] for time in lst]
            df['Gmt time'] = pd.to_datetime(df['Gmt time'])
            df = df.set_index('Gmt time')
            return df
        
        df = pd.read_csv(self.df_name)
        #df = convert_btc_df_dates_to_index(df)
        self.df = df
        self.NP_CUTOFF_VALUE = int(self.NP_CUTOFF_PCT * len(self.df))

        pretrained_model_name = self.check_pretrained_model_exists()
        if pretrained_model_name != None:
            self.load_model(pretrained_model_name)
            self.loaded_pretrained_model = True
    
    def get_moving_averages(self, df, normalize=True):
        mtx = [[0] * len(self.window_sizes) for _ in range(len(df))]
        for i in range(len(df)):
            for j in range(len(self.window_sizes)):
                if i-self.window_sizes[j]+1 < 0:
                    moving_average = sum(df['Close'][:self.window_sizes[j]+1]) / (i+1)
                else:
                    moving_average = sum([df['Close'][k] for k in range(i-self.window_sizes[j]+1, i+1)]) / self.window_sizes[j]
                
                # normalization
                if normalize:
                    moving_average = moving_average / df['Close'][i]
                
                mtx[i][j] = moving_average

        return mtx

    def get_profit(self, df, normalize=True):
        profits = []
        for i in range(len(df)):
            profit = None
            ini = df['Open'].iloc[i]
            for j in range(1, len(df)+1):
                if i + j >= len(df['Open']):
                    profit = 0
                    break
                if df['Open'].iloc[i+j] <= ini * (1.0 - self.SLPERC):
                    profit = df['Open'].iloc[i+j] - ini
                    break
                elif df['Open'].iloc[i+j] >= ini * (1.0 + self.TPPERC):
                    profit = df['Open'].iloc[i+j] - ini
                    break

            if profit != None:
                # normalization
                if normalize:
                    profit = profit / ini
                
                profits.append(profit)
            else:
                profits.append(0)
    
        return profits

    def initialize_window_signaler(self):
        high = list(self.df['High'])
        low = list(self.df['Low'])
        self.df['Volatility'] = [hi - li for hi, li in zip(high, low)]

        mtx = self.get_moving_averages(self.df, True)
        print("LEN MTX", mtx[0])
        profit = self.get_profit(self.df, True)
        print("LEN PROFIT", len(profit))

        # add to df
        for i in range(len(mtx[0])):
            self.df['MA'+str(self.window_sizes[i])] = np.array(mtx)[:, i]

        self.X = np.array(mtx)
        self.y = np.reshape(np.array(profit), (len(profit), 1))

        return 
    
    
    def btc_signal(self, global_pos, info, CUTOFF_LOWER, CUTOFF_UPPER):
        # global_pos must be global
        pred = self.REG.predict(self.X[global_pos:global_pos+1])
        threshold_lower = self.MEAN + (self.STD_DEV * CUTOFF_LOWER)
        threshold_upper = self.MEAN + (self.STD_DEV * CUTOFF_UPPER)
        if threshold_lower <= pred[0] <= threshold_upper:
            return True
        return False

    def btc_total_signal(self, X_test_index, info):
        global_pos = X_test_index + self.NP_CUTOFF_VALUE
        dg = self.btc_signal(global_pos, info, self.CUTOFF_LOWER, self.CUTOFF_UPPER)
        if dg:
            return 2

        if self.shorts:
            dg = self.btc_signal(global_pos, info, -self.CUTOFF_UPPER, -self.CUTOFF_LOWER)
            if dg:
                return 1
        return 0

    def train_model_for_backtesting(self):
        # Only use a fraction of the data when training for backtest purposes
        print("NP_CUTOFF_VALUE:", self.NP_CUTOFF_VALUE)
        REMAINING_VALUE = len(self.df) - self.NP_CUTOFF_VALUE
        X_train, X_test, y_train, y_test = self.X[:self.NP_CUTOFF_VALUE], self.X[-REMAINING_VALUE:], self.y[:self.NP_CUTOFF_VALUE], self.y[-REMAINING_VALUE:]
        # BAD: X_train, X_test, y_train, y_test = train_test_split(X, y)
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        
        if self.loaded_pretrained_model == False:
            print("Current time A:", datetime.now().strftime("%H:%M:%S"))
            self.REG.fit(X_train, y_train)
            print("Current time B:", datetime.now().strftime("%H:%M:%S"))

        score = self.REG.score(X_test, y_test)
        print("Score:", score)

        # Generate predictions for data s.t. mean and std_dev can be calculated
        y_train_pred = self.REG.predict(X_train)
        mean = (sum(y_train_pred)/len(y_train_pred))
        std_dev = math.sqrt(sum([(xi - mean)**2 for xi in y_train_pred])/len(y_train_pred))
        
        self.MEAN = mean
        self.STD_DEV = std_dev
        print(f"mean: {mean}, std_dev: {std_dev}")
        return 

    def initialize_window_signaler_for_backtesting(self):
        self.initialize_window_signaler()
        self.train_model_for_backtesting()
        df_btc_backtest = self.df
        if 'Volume BTC' in df_btc_backtest.columns:
            df_btc_backtest = df_btc_backtest.drop(['Volume BTC'], axis=1)
        if 'Volume' in df_btc_backtest.columns:
            df_btc_backtest = df_btc_backtest.drop(['Volume'], axis=1)
            
        print("df_btc_backtest.columns:", df_btc_backtest.columns)
        
        
        REMAINING_VALUE = len(self.df) - self.NP_CUTOFF_VALUE
        df_btc_backtest = df_btc_backtest.iloc[-REMAINING_VALUE:]
        print("len(df_btc_backtest):", len(df_btc_backtest))
        return self.df_name, df_btc_backtest

    def generate_model_name(self):
        
        ws = json.dumps(self.window_sizes)
        ws = re.sub(", ", "-", ws)
        ws = re.sub("\[", "#", ws)
        ws = re.sub("\]", "#", ws)
        shorts = 'false'
        if self.shorts:
            shorts = 'true'
        model_name = [self.df_name.split(".")[0], str(self.SLPERC), str(self.TPPERC), str(self.CUTOFF_LOWER), str(self.CUTOFF_UPPER), str(self.NP_CUTOFF_VALUE), shorts, ws]
        model_name = "_".join(model_name)
        return model_name

    def save_model(self, results):
        model_name = self.generate_model_name()
        joblib.dump(self.REG, f'models/{model_name}.pkl')
        print(f"Model: {model_name} saved.")

    def check_pretrained_model_exists(self):
        model_name = self.generate_model_name()
        for existing_model_name in os.listdir('models'):
            if model_name + ".pkl" == existing_model_name:
                return existing_model_name
        return None

    def load_model(self, model_name):
        self.REG = joblib.load('models/' + model_name)
    
    