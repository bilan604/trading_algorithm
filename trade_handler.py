import time
import random
from json import dumps
from datetime import datetime, timezone
from trading_bot import TradingBot


class Position(object):
    def __init__(self, entry_price, shares, date, slperc, tpperc, commision, short):
        self.entry_price = entry_price # price before commision
        self.shares = shares
        self.date = date
        self.slperc = slperc
        self.tpperc = tpperc
        self.commision = commision
        self.short = short
        self.proceed = True # should proceed
        self.not_proceed_reason = ""


class TradeHandler:

    def __init__(self, model, client, margin, trade_size):
        self.model = model # the trading bot
        self.client = client # coinbase API's client
        self.margin = margin # leverage
        self.trade_size = trade_size # float: the maximum proportion of the cash the bot is allowed to use in one trade

        self.current_position = [] # to override the model's current position
        self.acceptable_commision_rate = 0.01 # what range of yesterday's close

        self.initialize()
    
    def initialize(self):
        valid_load = self.load_current_position()
        if valid_load == False:
            self.proceed = False
            self.not_proceed_reason = "non-valid load on initialization()"

    def generate_client_order_id(self):
        new_order_id = ""
        for i in range(15):
            new_order_id += str(random.randint(1, 9))
        return new_order_id

    def get_orders(self):
        orders = self.client.list_orders()
        orders = orders.to_dict()
        print(orders['orders'])    
        return orders

    def get_open_orders(self):
        orders = self.get_orders()
        open_orders = []
        for order in orders['orders']:
            if order['status'] == 'OPEN':
                open_orders.append(order)
        return open_orders

    def get_portfolio_uuid(self):
        portfolios = self.client.get_portfolios()
        portfolios = portfolios.to_dict()
        for portfolio in portfolios['portfolios']:
            if portfolio['name'] == 'Default':
                return portfolio['uuid']
        return None

    def get_portfolio_spot_positions(self, uuid):
        portfolio = self.client.get_portfolio_breakdown(uuid)
        portfolio = portfolio.to_dict()
        spot_positions = portfolio['breakdown']['spot_positions']
        print(spot_positions)
        return spot_positions

    def get_fiat_value_of_asset(self, asset_name) -> float:
        # warning: CAD and USD
        # returns the fiat value of asset in portfolio: 
        uuid = self.get_portfolio_uuid()
        portfolio = self.client.get_portfolio_breakdown(uuid) # shouldn't be hard coded
        portfolio = portfolio.to_dict()
        spot_positions = portfolio['breakdown']['spot_positions']
        for spot_position in spot_positions:
            if spot_position['asset'] == asset_name:
                fiat_balance = spot_position['total_balance_fiat']
                fiat_currency = spot_position['cost_basis']['currency']
                if fiat_currency != "USD":
                    print(f"Error, fiat value of asset: {asset_name} is being returned in the non-usd currency:", fiat_currency)
                    return None
                return fiat_balance
        return None

    def get_crypto_value_of_asset(self, asset_name) -> float:
        # returns the USD fiat value of asset in portfolio
        uuid = self.get_portfolio_uuid()
        portfolio = self.client.get_portfolio_breakdown(uuid) # shouldn't be hard coded
        portfolio = portfolio.to_dict()
        spot_positions = portfolio['breakdown']['spot_positions']
        for spot_position in spot_positions:
            if spot_position['asset'] == asset_name:
                crypto_balance = spot_position['total_balance_crypto']
                return crypto_balance
        return None

    def log_order(order_id, side, btc_usdc_price, limit_price, stop_trigger_price, path="logs/orders.txt"):
        order_id = str(order_id)
        side = str(side) # its already a string but for consistency
        btc_usdc_price = str(btc_usdc_price)
        limit_price = str(limit_price)
        stop_trigger_price = str(stop_trigger_price)
        updatedISO = datetime.now(timezone.utc).isoformat()
        obj = {
            "order_id": order_id,
            "side": side,
            "btc_usdc_price": btc_usdc_price,
            "limit_price": limit_price,
            "stop_trigger_price": stop_trigger_price,
            "updatedISO": updatedISO
        }
        with open(path, "a") as f:
            line = dumps(obj)
            f.write(line)

    def get_product_price(self, product_name) -> float: # in USDC
        product = self.client.get_product(product_name)
        product_price = float(product["price"])
        return product_price

    def get_btc_price(self):
        return self.get_product_price("BTC-USDC")

    def buy_bitcoin(self, usd_amount: float):  
        # bitcoin precision: 8
        # usd precision: 2
        ####
        STILL_TESTING = True
        if STILL_TESTING == True:
            print("EARLY RETURN, STILL TESTING buy_bitcoin()")
            return False

        # use client to buy BTC-USDC, quote_size in USDC
        new_order_id = self.generate_client_order_id()
        available_usdc = self.get_crypto_value_of_asset("USDC")
        quote_size = round(available_usdc * self.trade_size, 2) # precision of 2 required for usdc
        if quote_size < 1.0:
            print("\nERROR: QUOTE SIZE LIKELY TOO SMALL:", str(quote_size))
            return False

        order = self.client.market_order_buy(
            client_order_id=new_order_id,
            product_id="BTC-USDC",
            quote_size=str(quote_size)
        )
        # TODO: log order
        if order['success']:
            order_id = order['success_response']['order_id']
            btc_usdc_price = self.get_btc_price()
            side = 'BUY'
            self.log_order(order_id, side, btc_usdc_price, None, None)

            #fills = self.client.get_fills(order_id=order_id)
            #dumps(fills.to_dict())
        else:
            error_response = order['error_response']
            print("\n---------------->Error processing order in buy_bitcoin():")
            print(error_response)
            return False

        return True

    def place_sl_tp_sell_order(self, btc_usdc_price):
        ####
        STILL_TESTING = True
        if STILL_TESTING == True:
            print("EARLY RETURN, STILL TESTING place_sl_tp_sell_orders()")
            return 

        new_order_id = self.generate_client_order_id()
        # trigger_bracket_order_gtc_sell:
        # places a sell order that triggers at tp and sl
        available_btc = self.get_crypto_value_of_asset("BTC")
        base_size = round(available_btc, 8)
        
        limit_price = btc_usdc_price * (1.0 + self.model.TPPERC)
        limit_price = round(limit_price, 2) # in USDC

        stop_trigger_price = btc_usdc_price * (1.0 - self.model.SLPERC)
        stop_trigger_price = round(stop_trigger_price, 2) # in USDC
        
        order  = self.client.trigger_bracket_order_gtc_sell(
            client_order_id=new_order_id,
            product_id='BTC-USDC',
            base_size=str(base_size),
            limit_price=str(limit_price), # +4%
            stop_trigger_price=str(stop_trigger_price), #-4% 
        )

        # TODO: log order
        if order['success']:
            order_id = order['success_response']['order_id'] # i.e. '383efe66-2a5d-415a-8103-bdf8228c518e'
            side = 'SELL'
            self.log_order(order_id, side, btc_usdc_price, limit_price, stop_trigger_price)
            #fills = self.client.get_fills(order_id=order_id)
            #dumps(fills.to_dict())
        else:
            error_response = order['error_response']
            print("\n---------------->Error processing order in place_sl_tp_sell_order():")
            print(error_response)
            return False
    
        return True

    def calculate_cash(self) -> float:
        # calculate the FIAT amount of the asset being used as balance for buying bitcoin (i.e. USD, USDC, USDT) 
        cash = self.get_crypto_value_of_asset('USDC')
        return cash

    def handle_trade(self):
        # 1. ToDo check the price of bitcoin is good
        pass
        # 2. Place a market order to bitcoin
        cash = self.calculate_cash()
        if cash == None:
            print("...")
            return False

        # trade_size should be under 1.0 or price fluctuations could cause
        # buy orders to not go through
        trade_amount = cash * self.trade_size

        buy_order_success = None
        sell_order_success = None
        buy_order_success = self.buy_bitcoin(trade_amount)
        if buy_order_success == True:
            # grab the price before waiting
            btc_usdc_price = self.get_btc_price()
            # wait a few seconds so the order can be processed
            time.sleep(10)
            sell_order_success = self.place_sl_tp_sell_order(btc_usdc_price)
            
        return buy_order_success, sell_order_success

    def handle_new_day(self):
        # this function triggers when a new day has arrived
        # and the btc csv has been updated with yesterday's information
        print("TradeHandler.handle_new_day() called")
        if self.proceed == False:
            print("\n------------>handle_new_day(): NOT PROCEEDING", self.not_proceed_reason)
            return
        
        self.model.initialize_window_signaler()
        self.model.train_model()

        idx_yesterday = len(self.model.df) - 1
        Xi = self.model.X[idx_yesterday:idx_yesterday+1] # moving averages and input for yesterday
        date = self.model.df['Gmt time'][idx_yesterday] # yesterday
        print("Predicting for date", date)

        # signal: 0 for pass, 1 for short, 2 for buy
        signal = self.model.btc_total_signal(idx_yesterday, is_global_index=True)

        # consider future selling if is good time to short, problem is no idea where the cutoffs should be yet

        if signal == 0:
            pass
        if signal == 1:
            pass
        if signal == 2:
            buy_order_success, sell_order_success = self.handle_trade()
            if not (buy_order_success and sell_order_success):
                self.proceed = False
                self.not_proceed_reason = "(buy_order_success, sell_order_success):" + f"({str(buy_order_success), {str(sell_order_success)}})"

    def get_open_orders(self):
        orders = self.get_orders()
        orders = [o for o in orders['orders'] if o['status'] == 'OPEN']
        return orders

    def check_valid_open_orders(self):
        open_orders = self.get_open_orders()
        if len(open_orders) == 0:
            return True
        if len(open_orders) == 1:
            if open_orders[0]['side'] == 'SELL':
                return True
            return False
        return False

    def get_latest_buy_order(self):
        orders = self.get_orders()
        for order in orders['orders'][::-1]:
            if order['side'] == 'BUY':
                return order
        return None

    def get_order_for_current_position(self):
        open_orders = self.get_open_orders()
        if not open_orders:
            return None
        
        order = open_orders[0]

        client_order_id = order['client_order_id']
        product_id = order['product_id']
        side = order['side'] # TODO: Add check for is SELL
        base_size = order['order_configuration']['trigger_bracket_gtc']['base_size']
        limit_price = order['order_configuration']['trigger_bracket_gtc']['limit_price']
        stop_trigger_price = order['order_configuration']['trigger_bracket_gtc']['stop_trigger_price']
        created_time = order['created_time']
        obj = {
            "client_order_id": client_order_id,
            "product_id": product_id,
            "side": side,
            "base_size": base_size,
            "limit_price": limit_price,
            "stop_trigger_price": stop_trigger_price,
            "created_time": created_time
        }
        return obj


    def load_current_position(self):
        # returns: successful, whether code should continue execution
        is_valid = self.check_valid_open_orders()
        if is_valid == False:
            return False
        
        buy_order = self.get_latest_buy_order()
        if buy_order == None:
            return False
        
        open_order = self.get_order_for_current_position()
        if open_order == None:
            return True
        
        # add check to make sure not buy_order['created_time'] > sell order created time
        created_time = datetime.fromisoformat(buy_order['created_time'])
        position = Position(entry_price=buy_order['average_filled_price'], \
                shares=buy_order['filled_size'], \
                    date=created_time, \
                        slperc=self.model.SLPERC, tpperc=self.model.TPPERC, \
                            commision=None, \
                                short=False)
        
        self.current_position = [position]
        self.model.current_position = [position]
        return True












