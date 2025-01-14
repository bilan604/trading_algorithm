from testing import *


def get_env(path=".env"):
    env = {}
    with open(path, "r") as f:
        for line in f.readlines():
            if not line.strip():
                continue
            if line[0] == "#":
                continue
            items = line[:-1].split("=")
            name = items[0]
            value = "=".join(items[1:])
            env[name] = value
    return env


if __name__ == '__main__':
    # using the backtest library, comparison of my trading algorithm v.s. michael harris trading method
    results = run_backtest()
    # compares XGBot against highest returning bot of 1000 randomly trading bots
    multitest()
    # simulates trading with Michael Harris indicator
    simulate_michael_harris()
    # compares XGBot against randomly trading bot
    simulate_both()
    # min, max, and average stats of 35 XGBots on different train/test split sizes
    view_spread()
    