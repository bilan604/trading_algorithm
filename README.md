# A BTC Trading Bot: XGBot  

## Personal Notes:  

Theres a conflict with urllib3 package for cdp-sdk (requires urllib > 2.3.0) and the urllib3 version requirements for google-auth (unused in this project anyways)  

## How XGBot works:  

The bot trades based on a daily basis based on the moving averages (for a bunch of different window sizes) for the day. Every day once the day has closed, the moving averages are generated and the bot makes a guess on how much it would earn / lose if it opened up a new position.  

When it opens up a new position, it buys BTC using USDC (0% transfer fee) and places two sell orders - one at TP_PERC above the closing price and one at SL_PERC below the closing price. The only way the bot exits the position is if the price of BTC shifts to one of the margins and a sell order is triggered.  

The BTC data is split into a training set and a testing set where the bot is trained only on data before a certain timeframe and tested on data after a certain timeframe. For each day, the training inputs are the moving averages for the day, and the outputs are how much it would have made if it opened up a new position.  

In actually buying bitcoin, the bot trades USDC for BTC on Coinbase. The bot trades only using the USDC readily available, meaning USDC must be manually bought to fund the bot. This is implemented as such so the bot can only use cash in the from USDC the account already owns, as opposed to cash directly from a bank account.   

## XGBot Variables (Hyperparameters):  

<b>NP_CUTOFF_PCT</b>:  
The fraction of data (in the range [0.0, 1.0]) to be used for training. Everything else will be used for testing. Setting this variable closer to 1.0 means more data will be used for training and at the same time there is less time to trade since less of the data is used for testing.  

Increasing NP_CUTOFF_PCT also tends to decrease the number of trades the bot is willing to make for a given CUTOFF_LOWER.  

<b>CUTOFF_LOWER</b>:  
The minimum standard deviations above the mean of its' predictions in the training dataset that the profit prediction for the current day (in the testing dataset) must be to trigger the bot to open a new position.  

Increasing CUTOFF_LOWER slightly increases it's winrate, but makes the bot trade much less frequently.  

<b>CUTOFF_UPPER</b>:  
The maximum standard deviations above the mean of its' predictions in the training dataset that the profit prediction for the current day (in the testing dataset) must be to trigger the bot to open a new position.  

This is generally just set to 100 so the bot takes all trades above CUTOFF_LOWER. The only reason this variable exists was to prevent anomalies from making the bot take trades, but it seems like the bot makes more taking as many trades as possible.  

<b>SL_PERC</b>:  
The fraction (in the range [0.0, 1.0]) below the buying price that a sell order should be placed for the sake of stop loss.  

For example, if SL_PERC is 0.04 and it buys a stock at $100.00 / share, it will place a sell order at $96.00.  

<b>TP_PERC</b>:  
The fraction (in the range [0.0, 1.0]) above the buying price that a sell order should be placed for the sake of taking profit.

For example, if TP_PERC is 0.04 and it buys a stock at $100.00 / share, it will place a sell order at $104.00.  

## Test Results:  

For 15 versions of the bot with NP_CUTOFF_PCT ranging from 80% to 95% (1% increment), CUTOFF_LOWER of 0.7, SL_PERC of 0.04, TP_PERC of 0.04, and window_sizes of [1, 3, 9, 15, 30, 60, 120, 240, 480, 960], the performance metrics are as seen below:  

```
---------------->KEY: Return %
MAX: 300.66239766365885
MIN: 24.746460721340156
AVG: 132.7726482551716


---------------->KEY: Max Drawdown %
MAX: 0.0
MIN: -14.095794338144024
AVG: -3.372566510064534


---------------->KEY: Winrate
MAX: 83.33333333333334
MIN: 64.15094339622641
AVG: 72.88666007110709


---------------->KEY: Start Cash
MAX: 10000
MIN: 10000
AVG: 10000.0


---------------->KEY: End Cash
MAX: 40066.239766365885
MIN: 12474.646072134015
AVG: 23277.264825517155


---------------->KEY: Total Trades
MAX: 56
MIN: 15
AVG: 31.933333333333334
```  

#### On average, the bot has 366.8 days (about a year) to trade, and returns +132%.  

#### The following is from when it has exactly one year to trade:  

```
------------------->XGBBot Simulation Results:
Total Snapshots: 20
Return Percentage: 101.6713240585551%
Maximum Drawdown: 0.0%
Winrate: 84.21052631578947%
Start Cash: 10000
End Cash: 20167.13240585551
Total Trades: 19
```  


## CDP API:  

It works.  


