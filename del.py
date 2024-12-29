

import pandas as pd
df= pd.read_csv("btc_data.csv")
df = df.drop(['Unnamed: 0'], axis=1)
df.to_csv('btc_data.csv', index=False)
print(df.columns)

