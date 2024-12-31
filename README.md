# Trading Bot  

The bot with parameters:

TEST_SLPERC = 0.05  
TEST_TPPERC = 0.05  
CUTOFF_LOWER=1.2  
CUTOFF_UPPER=100  
NP_CUTOFF_PCT=0.8  
shorts=False  

Has 96% precision on the DIRECTION predictions 1.2 standard deviations above the mean. If it thinks the chances of the price going up are >= Z=+1.2, then the price goes up 94% of the time.

Results of bot from view_spread() on btc_data_aggregated.csv:  
---------------->KEY: Return %  
MAX: 1550.8272284053216  
MIN: 52.8445547786233  
AVG: 292.3338382544663  
---------------->KEY: Max Drawdown %  
MAX: 0.0  
MIN: -16.031640442244353  
AVG: -1.7239365956008053  
---------------->KEY: Winrate  
MAX: 100.0  
MIN: 70.0  
AVG: 84.75510076224673  
---------------->KEY: Start Cash  
MAX: 10000  
MIN: 10000  
AVG: 10000.0  
---------------->KEY: End Cash  
MAX: 165082.72284053217  
MIN: 15284.45547786233  
AVG: 39233.38382544664  
---------------->KEY: Total Trades  
MAX: 62  
MIN: 8  
AVG: 33.714285714285715  

