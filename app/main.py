from flask import Flask, request, jsonify
import logging, os
from .trade import open_market_position, place_laddered_take_profits
from .config import WEBHOOK_SECRET

app = Flask(__name__)

logging.basicConfig(
    filename="/app/bot.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def check_secret(req):
    return req.headers.get("X-WEBHOOK-SECRET") == WEBHOOK_SECRET

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if not check_secret(request):
        return jsonify({'error': 'unauthorized'}), 401

    data = request.json
    symbol = data.get("ticker")
    direction = data.get("direction")
    qty = float(data.get("qty", 0.01))
    tp_percents = data.get("tp_targets", [1.01, 1.02, 1.04])
    sl_percent = data.get("sl", 0.99)
    entry_price = float(data.get("entry_price", 0))  # Should fetch real market price if not supplied

    try:
        if direction in ["open_long", "open_short"]:
            side = "Buy" if direction == "open_long" else "Sell"
            open_market_position(symbol, side, qty,
                                 take_profit=entry_price*tp_percents[0] if entry_price else None,
                                 stop_loss=entry_price*sl_percent if entry_price else None)
            if entry_price:
                place_laddered_take_profits(symbol, side, qty, entry_price, tp_percents)
        elif direction in ["close_long", "close_short"]:
            # Place a reduceOnly market order in the opposite direction
            side = "Sell" if direction == "close_long" else "Buy"
            open_market_position(symbol, side, qty)
        else:
            return jsonify({'error': 'unknown direction'}), 400
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
