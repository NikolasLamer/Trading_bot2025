from .bybit_api import bybit_request
import logging

def open_market_position(symbol, side, qty, take_profit=None, stop_loss=None):
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
    return bybit_request("POST", "/v5/order/create", payload, is_private=True)

def place_laddered_take_profits(symbol, side, total_qty, entry_price, tp_targets):
    # tp_targets = [1.01, 1.02, 1.04] for +1%, +2%, +4% for example
    qty_per_tp = round(total_qty / len(tp_targets), 4)
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
            bybit_request("POST", "/v5/order/create", payload, is_private=True)
        except Exception as e:
            logging.error(f"Laddered TP error for {symbol} at {tp_price}: {e}")

def set_trailing_stop(symbol, side, qty, activation_price, callback_rate):
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
    return bybit_request("POST", "/v5/order/create", payload, is_private=True)
