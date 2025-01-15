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
                 SLPERC=0.05, TPPERC=0.05, \
                 NP_CUTOFF_PCT=0.8, \
                 window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960],
                 shorts=False):
        
        self.name = "XGBBot"
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
        self.current_position = []  # for manual testing

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

        ########### HACKY
        # the following condition checks whether to skip loading a pretrained model
        # however, the model is recalculated for each test / everyday anyways
        # TODO: delete following condition?
        if "updating_btc.csv" in self.df_name:
            return

        # else try to load a pretrained model
        pretrained_model_name = self.check_pretrained_model_exists()
        if pretrained_model_name != None:
            print("\nMESSAGE: LOADING PRETRAINED MODEL\n")
            self.load_model(pretrained_model_name)
            self.loaded_pretrained_model = True
    
    def get_moving_averages(self, df, normalize=True):
        mtx = [[0] * len(self.window_sizes) for _ in range(len(df))]
        for j in range(len(self.window_sizes)):
            window_sum = 0
            for i in range(len(df)):
                if i < self.window_sizes[j]:
                    window_sum += df['Close'][i]
                    moving_average = window_sum / (i+1)
                else:
                    window_sum += df['Close'][i]
                    window_sum -= df['Close'][i-self.window_sizes[j]]
                    moving_average = window_sum / self.window_sizes[j]
                
                # normalization
                if normalize:
                    moving_average = moving_average / df['Close'][i]
                
                mtx[i][j] = moving_average
        
        return mtx

    def get_profit(self, df, normalize=True):
        profits = []
        for i in range(len(df)):
            profit = None
            ini = df['Close'].iloc[i]
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
        profit = self.get_profit(self.df, True)

        # add to df - does not affect self.X and self.y
        for i in range(len(mtx[0])):
            self.df['MA'+str(self.window_sizes[i])] = np.array(mtx)[:, i]

        self.X = np.array(mtx)
        self.y = np.reshape(np.array(profit), (len(profit), 1))

        return 
    
    def btc_signal(self, global_pos, CUTOFF_LOWER, CUTOFF_UPPER):
        # global_pos must be global
        X_i = self.X[global_pos:global_pos+1]
        pred = self.REG.predict(X_i)
        threshold_lower = self.MEAN + (self.STD_DEV * CUTOFF_LOWER)
        threshold_upper = self.MEAN + (self.STD_DEV * CUTOFF_UPPER)
        if threshold_lower <= pred[0] <= threshold_upper:
            return True
        return False

    def btc_total_signal(self, X_test_index, is_global_index=False):
        #### hacky
        if is_global_index:
            global_pos = X_test_index
        else:
            global_pos = X_test_index + self.NP_CUTOFF_VALUE
        
        dg = self.btc_signal(global_pos, self.CUTOFF_LOWER, self.CUTOFF_UPPER)
        if dg:
            return 2

        if self.shorts:
            dg = self.btc_signal(global_pos, -self.CUTOFF_UPPER * 1.3, -self.CUTOFF_LOWER * 1.3)
            if dg:
                return 1
        return 0

    def train_model(self):
        # Only use a fraction of the data when training for backtest purposes
        REMAINING_VALUE = len(self.df) - self.NP_CUTOFF_VALUE
        print("REMAINING_VALUE:", len(self.df) - self.NP_CUTOFF_VALUE, "(the amount of data not used for training)")
        X_train, X_test, y_train, y_test = self.X[:self.NP_CUTOFF_VALUE], self.X[-REMAINING_VALUE:], self.y[:self.NP_CUTOFF_VALUE], self.y[-REMAINING_VALUE:]
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        
        if self.loaded_pretrained_model == False: # maybe if I decide no need to retain
            self.REG.fit(X_train, y_train)

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

    def train_model_for_backtesting(self):
        # Only use a fraction of the data when training for backtest purposes
        REMAINING_VALUE = len(self.df) - self.NP_CUTOFF_VALUE
        print("REMAINING_VALUE:", len(self.df) - self.NP_CUTOFF_VALUE, "(the amount of data not used for training)")
        X_train, X_test, y_train, y_test = self.X[:self.NP_CUTOFF_VALUE], self.X[-REMAINING_VALUE:], self.y[:self.NP_CUTOFF_VALUE], self.y[-REMAINING_VALUE:]
        # BAD: X_train, X_test, y_train, y_test = train_test_split(X, y)
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        
        if self.loaded_pretrained_model == False:
            self.REG.fit(X_train, y_train)

        score = self.REG.score(X_test, y_test)
        print("Score:", score)

        # Generate predictions for data s.t. mean and std_dev can be calculated
        y_train_pred = self.REG.predict(X_train)
        mean = (sum(y_train_pred)/len(y_train_pred))
        std_dev = math.sqrt(sum([(xi - mean)**2 for xi in y_train_pred])/len(y_train_pred))
        
        self.MEAN = mean
        self.STD_DEV = std_dev
        #print(f"mean: {mean}, std_dev: {std_dev}")
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

    def initialize_window_signaler_for_testing(self):
        self.initialize_window_signaler()
        self.train_model_for_backtesting()

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
        print('\nLoaded saved model:', model_name)

    def check_precision(self):
        tp = 0
        fp = 0
        
        def pct_over_z(pred, mean, std, z=1.2):
            c = 0
            for yi in pred:
                if yi >= mean + (self.CUTOFF_LOWER * std):
                    c += 1
            return (c / len(pred)) * 100.0

        def check_frequency():

            train_pred = self.REG.predict(self.X_train)
            mean1 = sum(train_pred) / len(train_pred)
            std1 = (sum([(yi-mean1)**2 for yi in train_pred])/len(train_pred))**0.5

            test_pred = self.REG.predict(self.X_test)
            mean2 = sum(test_pred) / len(test_pred)
            std2 = (sum([(yi-mean2)**2 for yi in test_pred])/len(test_pred))**0.5

            c1 = pct_over_z(train_pred, mean1, std1)
            c2 = pct_over_z(test_pred, mean2, std2)
            print("\nPCT OF PREDICTIONS ABOVE CUTOFF FREQUENCY:")
            print("train:", c1)
            print("test:", c2)

        check_frequency()


        for i in range(len(self.y_test)):
            pred = self.REG.predict(self.X_test[i:i+1])
            if pred >= self.MEAN + (self.CUTOFF_LOWER * self.STD_DEV):
                if self.y_test[i][0] >= 0:
                    tp += 1
                else:
                    fp += 1

        print(f"\n---->Precision on {str(tp+fp)} preditions:", tp/(tp+fp))
        print("<-------------------------------------------")



