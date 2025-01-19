import time
import random
from json import dumps
from typing import Union
from datetime import datetime, timezone

from trading_bot import TradingBot

from helpers import VM_log

class Position(object):
    def __init__(self, entry_price, shares, date, slperc, tpperc, commision, short):
        self.entry_price = entry_price # price before commision
        self.shares = shares
        self.date = date
        self.slperc = slperc
        self.tpperc = tpperc
        self.commision = commision
        self.short = short


class TradeHandler:

    def __init__(self, model, client, margin, trade_size):
        self.model = model # the trading bot
        self.client = client # coinbase API's client
        self.margin = margin # leverage - unused
        self.trade_size = trade_size # float: the maximum proportion of the cash the bot is allowed to use in one trade

        self.current_position = [] # to override the model's current position
        self.acceptable_commision_rate = 0.01 # what range of yesterday's close
        
        self.proceed = True # should proceed
        self.not_proceed_reason = ""
        
        self.initialize()
    
    def initialize(self):
        valid_load = self.load_current_position()
        if valid_load == False:
            self.proceed = False
            self.not_proceed_reason = "non-valid load on initialization()"
            print("", self.not_proceed_reason)

    def generate_client_order_id(self):
        new_order_id = ""
        for i in range(15):
            new_order_id += str(random.randint(1, 9))
        return new_order_id

    def get_orders(self):
        orders = self.client.list_orders()
        orders = orders.to_dict()
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

    def get_crypto_value_of_asset(self, asset_name) -> Union[float, None]:
        # returns the value of asset in the asset itself - i.e. BTC: 0.0001
        uuid = self.get_portfolio_uuid()
        portfolio = self.client.get_portfolio_breakdown(uuid) # shouldn't be hard coded
        portfolio = portfolio.to_dict()
        spot_positions = portfolio['breakdown']['spot_positions']
        for spot_position in spot_positions:
            if spot_position['asset'] == asset_name:
                crypto_balance = spot_position['total_balance_crypto']
                return crypto_balance
        return None

    # TODO: figure out what this should be used for?
    def log_order(self, order_id, side, btc_usdc_price, limit_price, stop_trigger_price, comission_pct, path="logs/orders.txt"):
        order_id = str(order_id)
        side = str(side) # its already a string but for consistency
        btc_usdc_price = str(btc_usdc_price)
        limit_price = str(limit_price)
        stop_trigger_price = str(stop_trigger_price)
        comission_pct = str(comission_pct)
        updatedISO = datetime.now(timezone.utc).isoformat()
        obj = {
            "order_id": order_id,
            "side": side,
            "btc_usdc_price": btc_usdc_price,
            "limit_price": limit_price,
            "stop_trigger_price": stop_trigger_price,
            "comission_pct": comission_pct,
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
        # price in USDC/USD
        return self.get_product_price("BTC-USDC")

    def buy_bitcoin(self):  
        # usd precision: 2
        # bitcoin precision: 8

        # use client to buy BTC-USDC, quote_size in USDC
        new_order_id = self.generate_client_order_id()
        available_usdc = self.get_crypto_value_of_asset("USDC") # basically the amount of USD
        
        # self.trade_size should be under 1.0 or price 
        # fluctuations could cause buy orders to not go through
        quote_size = round(available_usdc * self.trade_size, 2) # precision of 2 required for usdc
        VM_log(f"--->Trade handler buy_bitcoin() called. Amount of BTC in USDC it will be buying: {str(quote_size)}")
        if quote_size < 1.0:
            print("\nERROR: QUOTE SIZE LIKELY TOO SMALL:", str(quote_size))
            VM_log(f"--->trade_handler will not be submitting the buy order as the quote_size was too small.\n")
            return False

        order = self.client.market_order_buy(
            client_order_id=new_order_id,
            product_id="BTC-USDC",
            quote_size=str(quote_size)
        )

        # TODO: figure out what to do after logging an order / with logged orders
        if order['success']:
            order_id = order['success_response']['order_id']
            btc_usdc_price = self.get_btc_price()
            side = 'BUY'
            self.log_order(order_id, side, btc_usdc_price, None, None, None, None)

            #fills = self.client.get_fills(order_id=order_id)
            #dumps(fills.to_dict())
            
            VM_log(f"--->trade handler successfully executed order to buy bitcoin. order_id: {order_id}, btc_usdc_price: {btc_usdc_price}\n")
        else:
            error_response = order['error_response']
            print("\n---------------->Error processing order in buy_bitcoin():")
            print(error_response)
            VM_log(f"--->trade handler was unsuccessful in executing order to buy bitcoin. error_response: {error_response}\n")
            return False

        return True

    def place_sl_tp_sell_order(self, btc_usdc_price):

        new_order_id = self.generate_client_order_id()
        # trigger_bracket_order_gtc_sell:
        # places a sell order that triggers at tp and sl
        available_btc = self.get_crypto_value_of_asset("BTC")
        base_size = base_size * 0.95
        base_size = round(available_btc, 8)
        
        limit_price = btc_usdc_price * (1.0 + self.model.TPPERC)
        limit_price = round(limit_price, 2) # in USDC

        stop_trigger_price = btc_usdc_price * (1.0 - self.model.SLPERC)
        stop_trigger_price = round(stop_trigger_price, 2) # in USDC
        
        VM_log(f"--->#### trade_handler is going to place a trigger bracket sell order #### available_btc: {str(available_btc)}, limit_price: {str(limit_price)}, stop_trigger_price: {stop_trigger_price}\n")

        order = self.client.trigger_bracket_order_gtc_sell(
            client_order_id=new_order_id,
            product_id='BTC-USDC',
            base_size=str(base_size),
            limit_price=str(limit_price), # +4%
            stop_trigger_price=str(stop_trigger_price), #-4% 
        )

        # TODO: figure out what to do after logging an order / with logged orders
        if order['success']:
            order_id = order['success_response']['order_id'] # i.e. '383efe66-2a5d-415a-8103-bdf8228c518e'
            side = 'SELL'
            self.log_order(order_id, side, btc_usdc_price, limit_price, stop_trigger_price, None)

            #fills = self.client.get_fills(order_id=order_id)
            #dumps(fills.to_dict())
            VM_log(f"--->trade handler submitted trigger bracket order for selling bitcoin. order_id: {order_id}\n")
        else:
            error_response = order['error_response']
            print("\n---------------->Error processing order in place_sl_tp_sell_order():")
            print(error_response)
            VM_log(f"--->trade_handler encountered an error placing a trigger bracket sell order. error_response: {error_response}.\n")
            return False
    
        return True

    def calculate_cash(self) -> float:
        # calculate the FIAT amount of the asset being used as balance for buying bitcoin (i.e. USD, USDC, USDT) 
        cash = self.get_crypto_value_of_asset('USDC')
        return cash

    def get_open_orders(self):
        orders = self.get_orders()
        orders = [o for o in orders['orders'] if o['status'] == 'OPEN']
        return orders

    def get_all_buy_orders(self):
        buy_orders = []
        orders = self.get_orders()
        for order in orders['orders']:
            if order['side'] == 'BUY':
                buy_orders.append(order)
        return buy_orders

    def get_all_sell_orders(self):
        sell_orders = []
        orders = self.get_orders()
        for order in orders['orders']:
            if order['side'] == 'SELL':
                sell_orders.append(order)
        return sell_orders

    def check_existing_open_buy_order(self):
        buy_orders = self.get_all_buy_orders()
        for buy_order in buy_orders:
            if buy_order['status'] != "FILLED":
                return True
        return False

    def check_should_cancel_open_buy_order(self):
        buy_orders = self.get_all_buy_orders()
        buy_orders = [bo for bo in buy_orders if bo['status'] != 'FILLED']
        for buy_order in buy_orders:
            dt1 = datetime.now(timezone.utc)
            dt2 = datetime.fromisoformat(buy_order['created_time'])
            diff = dt1 - dt2
            hours_elapsed = (diff.days * 24) + (diff.seconds // 3600)
            if hours_elapsed >= 12:
                return True
        return False

    # TODO: test this
    def cancel_open_buy_order(self):
        buy_orders = self.get_all_buy_orders()
        buy_orders = [bo for bo in buy_orders if bo['status'] != 'FILLED']
        for buy_order in buy_orders:
            dt1 = datetime.now(timezone.utc)
            dt2 = datetime.fromisoformat(buy_order['created_time'])
            diff = dt1 - dt2
            hours_elapsed = (diff.days * 24) + (diff.seconds // 3600)
            if hours_elapsed >= 12:
                #cancel buy position
                self.client.cancel_orders([buy_order['order_id']])
                VM_log(f"--->trade_handler cancelled open buy order (order_id: {buy_order['order_id']}) since it was not filled in 12 hours.\n")
                return True
        
        return False

    def check_exists_multiple_open_buy_orders(self):
        buy_orders = self.get_all_buy_orders()
        buy_orders = [bo for bo in buy_orders if bo['status'] != "FILLED"]
        return len(buy_orders) > 1

    def check_valid_open_sell_orders(self):
        open_orders = self.get_open_orders()
        open_orders = [oo for oo in open_orders if oo['side'] == "SELL"]
        if len(open_orders) == 0:
            return True
        if len(open_orders) == 1:
            return True
        return False

    def get_latest_closed_buy_order(self, product_id='BTC-USDC'):
        # FILLED / OPEN
        orders = self.get_orders()
        for order in orders['orders']:
            if order['side'] == 'BUY' and order['status'] != 'FILLED' and order['product_id'] == product_id:
                return order
        return None
    
    def get_open_sell_order_for_current_position(self):
        open_orders = self.get_open_orders()
        open_orders = [oo for oo in open_orders if oo['side'] == "SELL"] # only the sell orders
        if not open_orders:
            return None
        
        order = open_orders[0]

        client_order_id = order['client_order_id']
        product_id = order['product_id']
        side = order['side']
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
        # run a check to ensure there is only 0 or 1 open sell order
        is_valid = self.check_valid_open_sell_orders()
        if is_valid == False:
            return False
        
        open_sell_order = self.get_open_sell_order_for_current_position()

        if open_sell_order == None:
            # theres no sell order, so self.current_position should be empty list
            return True
        else:
            closed_buy_order = self.get_latest_closed_buy_order(open_sell_order['product_id'])
            created_time = datetime.fromisoformat(closed_buy_order['created_time'])
            position = Position(entry_price=closed_buy_order['average_filled_price'], \
                    shares=closed_buy_order['filled_size'], \
                        date=created_time, \
                            slperc=self.model.SLPERC, tpperc=self.model.TPPERC, \
                                commision=None, \
                                    short=False)
            
            self.current_position = [position]
            self.model.current_position = [position]
            VM_log(f"--->trade_handler loaded a current position. shares: {str(position.shares)}, slperc: {position.slperc}, tpperc: {position.tpperc}, date: {str(position.date)}, commision: {str(position.commision)}.\n")
            return True

    def handle_trade(self):
        VM_log(f"--->trade_handler's handle_trade() function was called.\n")

        # TODO: This code doesn't seem to be used?
        cash = self.calculate_cash()
        if cash == None:
            print("...")
            return False

        buy_order_success = None
        sell_order_success = None
        buy_order_success = self.buy_bitcoin()
        print(f"\n\n\n------------------------------------------------\n\
              ATTEMPTED TO EXECUTE A BUY ORDER\n    ->buy_order_success: {buy_order_success}\n\
                ------------------------------------------------\n\n\n")
        VM_log(f"--->#### ATTEMPTED TO EXECUTE A BUY ORDER ####. buy_order_success: {buy_order_success}")
        
        if buy_order_success == True:
            # grab the price before waiting
            btc_usdc_price = self.get_btc_price()
            # wait a few seconds so the order can be processed
            print("\nSLEEPING FOR 30 SECONDS.")
            time.sleep(10)
            sell_order_success = self.place_sl_tp_sell_order(btc_usdc_price)
            print(f"\n\n\n------------------------------------------------\n\
                  ATTEMPTED TO EXECUTE A SELL ORDER\n    ->sell_order_success: {sell_order_success}\n\
                    ------------------------------------------------\n\n\n")
            VM_log(f"--->#### ATTEMPTED TO EXECUTE A SELL ORDER####. sell_order_success: {sell_order_success}")

        return buy_order_success, sell_order_success

    def handle_new_day(self) -> None:
        # this function triggers when a new day has arrived
        # and the btc csv has been updated with yesterday's information
        print("TradeHandler.handle_new_day() called")
        VM_log(f"--->TradeHandler.handle_new_day() called")
        
        # If there are multiple open buy orders then either the bot 
        # did something wrong or I created buy order(s) on coinbase manually
        # (because I forgot that would affect the bot's code)
        # The bot should not proceed in such case
        if self.check_exists_multiple_open_buy_orders():
            self.proceed = False
            self.not_proceed_reason = "self.check_exists_multiple_open_buy_orders() returned True. Not proceeding in self.handle_day() as there exist multiple open buy orders."
            raise Exception(self.not_proceed_reason)

        # If the handler is currently in a position, it should not be trading yet
        if self.current_position:
            # refresh self.current_position, if the position has been closed then it can trade again
            valid_load = self.load_current_position()
            # If the handler did not load a valid current position, raise Exception
            if valid_load == False:
                self.proceed = False
                self.not_proceed_reason = "self.load_current_position() returned False. Not proceeding in self.hanle_day() as position was not loaded successfully."
                raise Exception(self.not_proceed_reason)
            
            # After refresh: If the handler is currently in a position, it should not be trading yet
            if self.current_position:
                return
            
            VM_log(f"---> #### trade_handler's current position was cleared #### indicating that tigger bracket sell order was executed.\n")
        else:
            # The code reaches here only if trade_handler's current_position is empty list
            # current_position is only set if there exists an open sell order and a closed buy order (in self.load_current_position())

            # however, the code will reach here if there is an open sell order but no closed buy order
            # this would likely be due to manually making purchases on coinbase

            # the following code checks for old OPEN buy orders, and cancels them
            exists_open_buy_order = self.check_existing_open_buy_order()
            if exists_open_buy_order == True:
                # check whether the buy order was made over 12 hours ago
                is_expired_buy_order = self.check_should_cancel_open_buy_order()
                VM_log("---> #### trade_handler does not have a current position (indicating no (closed buy order and open sell order)), but there exists an open buy order. #### Checking whether to cancel it.\n")
                
                # if the buy order is expired, it should be cancelled
                if is_expired_buy_order == True:
                    self.cancel_open_buy_order()

                    time.sleep(45)

                    # one last check to make sure
                    exists_open_buy_order = self.check_existing_open_buy_order()
                    if exists_open_buy_order == True:
                        self.proceed = False
                        self.not_proceed_reason = "Attempted to cancel existing open buy order as it was made over 12 hours ago, yet checking self.check_existing_open_buy_order() returned True after attempt to cancel."                        
                        raise Exception(self.not_proceed_reason)
                    
                    # here the code will have successfully cancelled an open and expired buy order
                    # the code should continue
                    pass

                else:
                    # There is an open buy order and it is not expired
                    #print("return due to existing open buy order")
                    return
            else:
                # The code reaches here if there is no open buy order: the expected norm
                pass
            
        # self.proceed can be set to false at any time to prevent the bot from proceeding 
        if self.proceed == False:
            print("\n------------>handle_new_day(): NOT PROCEEDING:")
            raise Exception(self.not_proceed_reason)
        
        VM_log(f"--->All safety checks passed in handle_new_day. Will be retraining model and generating signal.\n")

        self.model.initialize_window_signaler()
        # TODO: Determine whether to retrain the model every single day
        self.model.train_model()

        idx_yesterday = len(self.model.df) - 1
        
        Xi = self.model.X[idx_yesterday:idx_yesterday+1] # moving averages and input for yesterday
        date = self.model.df['Gmt time'][idx_yesterday] # yesterday
        print("\n------------------------------->handle_new_day():")
        print("Xi (Prediction Row):", Xi)
        print("Date:", date)
        print("idx_yesterday (prediction index on dataframe):", idx_yesterday)

        # signal: 0 for pass, 1 for short, 2 for buy
        signal = self.model.btc_total_signal(idx_yesterday, is_global_index=True)
        VM_log(f"--->The trade_handler generated the signal ({str(signal)}) for yesterday ({str(date)}).\n")

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
                raise Exception(self.not_proceed_reason)

        return






