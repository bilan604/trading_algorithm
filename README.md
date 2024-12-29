# Trading Bot  

The bot with parameters:

TEST_SLPERC = 0.05
TEST_TPPERC = 0.05
CUTOFF_LOWER=1.2
CUTOFF_UPPER=100
NP_CUTOFF_PCT=0.8
shorts=False

Has 96% precision on the DIRECTION predictions 1.2 standard deviations above the mean. If it thinks the chances of the price going up are >= Z=+1.2, then the price goes up 94% of the time.

