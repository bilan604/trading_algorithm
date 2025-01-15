

def append_coinmarketcap_data_to_updating_btc_csv(coinmarketcap_name, updating_btc_csv_name):
    import pandas as pd
    import numpy as np
    from datetime import datetime, timezone


    updating_colnames = ["Gmt time","Open","High","Low","Close"]

    df = pd.read_csv(coinmarketcap_name, delimiter=";")
    df.rename(columns={'timeOpen': 'Gmt time', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)

    df = pd.DataFrame({colname: df[colname] for colname in updating_colnames})

    def fix_times(col):
        lst = []
        for i in range(len(col)):
            date_str = col[i]
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            date_obj = str(date_obj)
            lst.append(date_obj)
        return lst

    df['Gmt time'] = fix_times(df['Gmt time'])
    # round prices to 2
    for round_col in ["Open","High","Low","Close"]:
        df[round_col] = list(map(lambda x: round(x, 2), df[round_col]))

    df = df.iloc[::-1]

    df_updating = pd.read_csv(updating_btc_csv_name)
    last_recorded_time = df_updating['Gmt time'].iloc[len(df_updating)-1]
    last_recorded_dt = datetime.strptime(last_recorded_time, '%Y-%m-%d %H:%M:%S')
    dd = {colname: [] for colname in updating_colnames}
    for i in range(len(df)):
        curr_dt = datetime.strptime(df['Gmt time'].iloc[i], '%Y-%m-%d %H:%M:%S')
        diff = curr_dt - last_recorded_dt
        if diff.days >= 1:
            for colname in updating_colnames:
                dd[colname].append(df[colname].iloc[i])

    df_2 = pd.DataFrame(dd)
    df_concat = pd.concat([df_updating, df_2], ignore_index=True)
    df_concat.to_csv(updating_btc_csv_name, index=False)


# update the updating_btc.csv file with csv downloaded from https://coinmarketcap.com/currencies/bitcoin/historical-data/
#coinmarketcap_name = "Bitcoin_11_13_2024-1_14_2025_historical_data_coinmarketcap.csv"
#updating_btc_csv_name = "csvs/updating_btc.csv"
#append_coinmarketcap_data_to_updating_btc_csv(coinmarketcap_name, updating_btc_csv_name)
