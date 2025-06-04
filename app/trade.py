from .bybit_api import bybit_request
import logging
import math

def get_account_equity(coin="USDT"):
    r = bybit_request("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"}, is_private=True)
    wallets = r['result']['list'][0]['coin']
    for w in wallets:
        if w['coin'] == coin:
            return float(w['equity'])
    raise Exception(f"Coin {coin} not found in wallet.")

def get_symbol_precision(symbol):
    r = bybit_request("GET", "/v5/market/instruments-info", {"category": "linear", "symbol": symbol})
    info = r['result']['list'][0]
    qty_step = float(info['lotSizeFilter']['qtyStep'])
    # Calculate decimal precision from step size
    qty_prec = abs(int(math.log10(qty_step))) if qty_step < 1 else 0
    return qty_step, qty_prec

def get_mark_price(symbol):
    r = bybit_request("GET", "/v5/market/tickers", {"category": "linear", "symbol": symbol})
    return float(r['result']['list'][0]['markPrice'])

def calculate_position_qty(symbol, percent=0.05):
    equity = get_account_equity()
    price = get_mark_price(symbol)
    usd_amt = equity * percent
    qty_step, qty_prec = get_symbol_precision(symbol)
    raw_qty = usd_amt / price
    # Round down to nearest allowed step
    qty = raw_qty - (raw_qty % qty_step)
    return round(qty, qty_prec)

def open_market_position(symbol, side, take_profit=None, stop_loss=None, percent=0.05):
    qty = calculate_position_qty(symbol, percent=percent)
    if qty <= 0:
        raise Exception("Calculated quantity is zero or less!")
    payload = {
        "category": "linear",
        "symbol": symbol,
        "side": side,  # "Buy" or "Sell"
        "orderType": "Market",
        "qty": str(qty),
        "timeInForce": "GTC"
    }
    if take_profit:
        payload["takeProfit"] = str(take_profit)
        payload["tpTriggerBy"] = "LastPrice"
    if stop_loss:
        payload["stopLoss"] = str(stop_loss)
        payload["slTriggerBy"] = "LastPrice"
    logging.info(f"Submitting order: {payload}")
    return bybit_request("POST", "/v5/order/create", payload, is_private=True)

def place_laddered_take_profits(symbol, side, entry_price, tp_targets, percent=0.05):
    qty = calculate_position_qty(symbol, percent=percent)
    if qty <= 0:
        raise Exception("Calculated quantity is zero or less for laddered TP!")
    qty_step, qty_prec = get_symbol_precision(symbol)
    num_targets = len(tp_targets)
    qty_per_tp = round(qty / num_targets, qty_prec)
    for tp_mult in tp_targets:
        tp_price = round(entry_price * tp_mult, 2)
        payload = {
            "category": "linear",
            "symbol": symbol,
            "side": "Sell" if side == "Buy" else "Buy",
            "orderType": "Limit",
            "qty": str(qty_per_tp),
            "price": str(tp_price),
            "timeInForce": "GTC",
            "reduceOnly": True
        }
        try:
            logging.info(f"Placing laddered TP: {payload}")
            bybit_request("POST", "/v5/order/create", payload, is_private=True)
        except Exception as e:
            logging.error(f"Laddered TP error for {symbol} at {tp_price}: {e}")

def set_trailing_stop(symbol, side, activation_price, callback_rate, percent=0.05):
    qty = calculate_position_qty(symbol, percent=percent)
    if qty <= 0:
        raise Exception("Calculated quantity is zero or less for trailing stop!")
    payload = {
        "category": "linear",
        "symbol": symbol,
        "side": "Sell" if side == "Buy" else "Buy",
        "orderType": "TrailingStopMarket",
        "qty": str(qty),
        "activationPrice": str(activation_price),
        "callbackRate": str(callback_rate),
        "reduceOnly": True
    }
    logging.info(f"Setting trailing stop: {payload}")
    return bybit_request("POST", "/v5/order/create", payload, is_private=True)
