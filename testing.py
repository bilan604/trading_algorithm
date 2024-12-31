import random

from trading_bot import TradingBot
from trading_bots.control_bots import *

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor



class Simulation(object):
    def __init__(self, cash, margin, commision, model, start_index, trading_size=0.1):
        self.cash = cash
        self.margin = margin
        self.commision = commision
        self.model = model
        self.start_index = start_index  # the index of the data in which trading should begin
        self.trading_size = trading_size

        self.snapshots = []

    def snapshot(self, won=None):
        snapshot = {
            'cash': self.cash,
            'margin': self.margin,
            'commision': self.commision,
            'won': won,
            'model_state': self.model.current_position,  # Storing current positions
            'time': self.model.df['Gmt time'][self.start_index]  # Time when the snapshot is taken
        }
        self.snapshots.append(snapshot)

    def display_stats(self, stats):
        print(f"\n------------------->{self.model.name} Simulation Results:")
        print("Total Snapshots:", len(self.snapshots))
        print(f"Return Percentage: {stats['Return %']}%")
        print(f"Maximum Drawdown: {stats['Max Drawdown %']}%")
        print(f"Winrate: {stats['Winrate']}%")
        print(f"Start Cash: {stats['Start Cash']}")
        print(f"End Cash: {stats['End Cash']}")
        print(f"Total Trades: {stats['Total Trades']}")

    def compare_start_and_end_snapshots(self):
        if len(self.snapshots) < 2:
            print("Not enough snapshots to compare.")
            return None

        # First snapshot
        start_snapshot = self.snapshots[0]
        start_cash = start_snapshot['cash']

        # Last snapshot
        end_snapshot = self.snapshots[-1]
        end_cash = end_snapshot['cash']

        # Calculate Return Percentage
        return_percentage = ((end_cash - start_cash) / start_cash) * 100.0

        # Maximum Drawdown
        # We'll iterate over the snapshots and calculate the drawdowns
        max_drawdown = (min([ss['cash'] - start_cash for ss in self.snapshots]) / start_cash) * 100
        
        # Winrate: We'll assume a "win" is when the cash at the end is greater than the cash at the beginning.
        winrate = (sum([1 if self.snapshots[i]['won'] == True else 0 for i in range(1, len(self.snapshots))]) / (len(self.snapshots)-1)) * 100

        # Summary statistics
        stats = {
            'Return %': return_percentage,
            'Max Drawdown %': max_drawdown,
            'Winrate': winrate,
            'Start Cash': start_cash,
            'End Cash': end_cash,
            'Total Trades': len(self.snapshots) - 1,
        }

        # Print or return the summary statistics
        self.display_stats(stats)

        return stats

    def start(self):
        self.snapshot(None)

        df = self.model.df
        for i in range(self.start_index, len(self.model.df)):
            # check should exit position
            if self.model.current_position:
                entry_price = self.model.current_position[0].entry_price
                shares = self.model.current_position[0].shares
                if df['Open'][i] >= (entry_price * (1.0 + self.model.TPPERC)):
                    self.cash += df['Open'][i] * shares
                    self.model.current_position = []
                    self.snapshot(True)
                elif df['Open'][i] <= (entry_price * (1.0 - self.model.SLPERC)):
                    self.cash += df['Open'][i] * shares
                    self.model.current_position = []
                    self.snapshot(False)

            total_signal = self.model.btc_total_signal(i, is_global_index=True)  # 0, 1, 2
            if total_signal == 0:
                continue
            elif total_signal == 1:
                if not self.model.shorts:
                    continue
                if self.model.current_position: # Prevents buying if a position is open
                    continue
                invest_amount = self.trading_size * self.cash
                price_per_share = df['Open'][i] * (1.0 + self.commision)
                shares = invest_amount / price_per_share
                pos = Position(df['Open'][i], shares, df['Gmt time'][i], self.model.SLPERC, self.model.TPPERC, self.commision, True)
                self.model.current_position.append(pos)

                self.cash -= invest_amount

            elif total_signal == 2:
                if self.model.current_position: # Prevents buying if a position is open
                    continue
                
                invest_amount = self.trading_size * self.cash
                price_per_share = df['Open'][i] * (1.0 + self.commision)
                shares = invest_amount / price_per_share
                
                pos = Position(df['Open'][i], shares, df['Gmt time'][i], self.model.SLPERC, self.model.TPPERC, self.commision, False)
                self.model.current_position.append(pos)

                self.cash -= invest_amount

        # sell if has position at the end
        if self.model.current_position:
            entry_price = self.model.current_position[0].entry_price
            shares = self.model.current_position[0].shares
            self.cash += df['Open'][len(df)-1] * shares
            if df['Open'][len(df)-1] > entry_price:
                won = True
            else:
                won = False
            self.snapshot(None)
        
        return

def simulate_both():
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    TEST_SLPERC = 0.05
    TEST_TPPERC = 0.05
    REG = GradientBoostingRegressor(random_state=0)
    m1 = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                    SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, \
                    NP_CUTOFF_PCT=0.85, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    m1.initialize_window_signaler_for_testing()

    m2 = ControlBot(df_name=df_btc_name, p = 0.05, SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, shorts=False)

    sim1 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                    model=m1, start_index=m1.NP_CUTOFF_VALUE, trading_size=1)
    sim2 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                    model=m2, start_index=m1.NP_CUTOFF_VALUE, trading_size=1)

    sim1.start()
    sim1.compare_start_and_end_snapshots()

    sim2.start()
    sim2.compare_start_and_end_snapshots()


def simulate_michael_harris():
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    TEST_SLPERC = 0.04
    TEST_TPPERC = 0.04
    m1 = MichaelHarris(df_name=df_btc_name, SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, shorts=False)
    NP_CUTOFF_VALUE = int(0.8 * len(m1.df))
    sim1 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                        model=m1, start_index=NP_CUTOFF_VALUE, trading_size=1)
    sim1.start()
    sim1.compare_start_and_end_snapshots()

def multitest():
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    TEST_SLPERC = 0.05
    TEST_TPPERC = 0.05
    REG = GradientBoostingRegressor(random_state=0)
    m1 = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                    SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, \
                    NP_CUTOFF_PCT=0.8, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    m1.initialize_window_signaler_for_testing()
    sim1 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                        model=m1, start_index=m1.NP_CUTOFF_VALUE, trading_size=1)
    sim1.start()
    results1 = sim1.compare_start_and_end_snapshots()

    results2 = None
    for i in range(1000):
        m2 = ControlBot(df_name=df_btc_name, p = 0.1, SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, shorts=False)
        sim2 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                        model=m2, start_index=m1.NP_CUTOFF_VALUE, trading_size=1)
        sim2.start()
        results = sim2.compare_start_and_end_snapshots()
        if not results2 or results['Return %'] > results2['Return %']:
            results2 = results
        
    print("\n-------------------> MULTISHOT COMPARISON:")
    sim1.display_stats(results1)
    sim2.display_stats(results2)


def see_trade_frequency_and_precision():
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    TEST_SLPERC = 0.05
    TEST_TPPERC = 0.05
    REG = GradientBoostingRegressor(random_state=0)
    m1 = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                    SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, \
                    NP_CUTOFF_PCT=0.9, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    m1.initialize_window_signaler_for_testing()
    m1.check_precision()

def simulate_XGBOT(np_cutoff_pct=0.8):
    df_btc_name = 'csvs/btc_data_aggregated.csv'
    TEST_SLPERC = 0.05
    TEST_TPPERC = 0.05
    REG = GradientBoostingRegressor(random_state=0)
    m1 = TradingBot(df_btc_name, REG, CUTOFF_LOWER=1.2, CUTOFF_UPPER=100, \
                    SLPERC=TEST_SLPERC, TPPERC=TEST_TPPERC, \
                    NP_CUTOFF_PCT=np_cutoff_pct, shorts=False, \
                    window_sizes=[1, 3, 9, 15, 30, 60, 120, 240, 480, 960])
    m1.initialize_window_signaler_for_testing()

    sim1 = Simulation(cash=10000, margin=1.0, commision=0.01, \
                    model=m1, start_index=m1.NP_CUTOFF_VALUE, trading_size=1)
    
    sim1.start()
    results = sim1.compare_start_and_end_snapshots()
    return results


def view_spread():
    # displays spread of performance on different training cutoffs
    def mma(rrs, key):
        print("MAX:", max(rss, key=lambda x: x[key])[key])
        print("MIN:", min(rss, key=lambda x: x[key])[key])
        print("AVG:", sum([rssi[key] for rssi in rss])/len(rss))

    rss = []
    for i in range(35):
        np_cutoff_pct = 0.6 + (0.01) * i
        print("np_cutoff_pct:", np_cutoff_pct)
        results = simulate_XGBOT(np_cutoff_pct)
        rss.append(results)

    for k in rss[0].keys():
        print("\n\n---------------->KEY:", k)
        mma(rss, k)

