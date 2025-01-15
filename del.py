# USED FOR TESTING ISOLATED CODE DURING DEVELOPMENT


def client_order_examples():

    from trade_handler import TradeHandler

    from coinbase.rest import RESTClient
    from json import dumps

    from helpers import get_env

    from helpers import get_btc_usd_price 

    api_key = get_env()["CDP_API_KEY"]
    api_secret = get_env()["CDP_API_KEY_PRIVATE_KEY"]

    client = RESTClient(api_key=api_key, api_secret=api_secret)
    th = TradeHandler(None, client, 1.0, 0.8)
    print("price 1:", get_btc_usd_price())
    product = client.get_product("BTC-USDC")
    btc_usdc_price = float(product["price"])
    print("price 2:", btc_usdc_price)

    # example
    available_btc = th.get_crypto_value_of_asset('BTC')
    base_size = round(0.33 * available_btc, 8)
    
    # examples of proper rounding for USDC
    limit_price = round(btc_usdc_price * (1.0 + 0.02), 2)
    stop_trigger_price = round(btc_usdc_price * (1.0 - 0.02), 2)

    def code_example_market_sell_bitcoin_into_usdc(th):
        # tested, works
        new_order_id = th.generate_client_order_id()
        order = client.market_order_sell(
            client_order_id=new_order_id,
            product_id="BTC-USDC",
            base_size=str(base_size)
        )

        if order['success']:
            order_id = order['success_response']['order_id']
            fills = client.get_fills(order_id=order_id)
            dumps(fills.to_dict())
        else:
            error_response = order['error_response']
            print(error_response)

    def code_example_trigger_bracket_order_gtc_sell(client, th):
        product = client.get_product("BTC-USDC")
        btc_usdc_price = float(product["price"])
        print("price 2:", btc_usdc_price)

        available_btc = th.get_crypto_value_of_asset('BTC')
        base_size = round(0.33 * available_btc, 8)
        limit_price = round(btc_usdc_price * (1.0 + 0.02), 2)
        stop_trigger_price = round(btc_usdc_price * (1.0 - 0.02), 2)


        # trigger_bracket_order_gtc_sell:
        # places a sell order that triggers at tp and sl
        new_order_id = th.generate_client_order_id()
        order = th.client.trigger_bracket_order_gtc_sell(
            client_order_id=new_order_id,
            product_id='BTC-USDC',
            base_size=str(base_size),
            limit_price=str(limit_price), # +4%
            stop_trigger_price=str(stop_trigger_price), #-4% 
        )

        if order['success']:
            order_id = order['success_response']['order_id']
            fills = client.get_fills(order_id=order_id)
            dumps(fills.to_dict())
        else:
            error_response = order['error_response']
            print(error_response)

        """
        # a sell limit order can only be executed at the limit price or HIGHER
        client.stop_limit_order_sell(
            client_order_id=,
            product_id=,
            base_size=,
            limit_price=,
            stop_price=,
            stop_direction=,
        )
        """



    print("Finished")





