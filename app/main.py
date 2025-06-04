from flask import Flask, request, jsonify
import logging
from .trade import open_market_position, place_laddered_take_profits, get_mark_price
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
    percent = float(data.get("percent", 0.05))  # Allow override for position size percent

    # Optional: accept ladder/TP/SL details or use default
    tp_percents = data.get("tp_targets", [1.01, 1.02, 1.04])
    sl_percent = data.get("sl", 0.99)
    entry_price = float(data.get("entry_price")) if data.get("entry_price") else get_mark_price(symbol)

    try:
        if direction in ["open_long", "open_short"]:
            side = "Buy" if direction == "open_long" else "Sell"
            tp_price = entry_price * tp_percents[0] if tp_percents else None
            sl_price = entry_price * sl_percent if sl_percent else None

            open_market_position(
                symbol,
                side,
                take_profit=tp_price,
                stop_loss=sl_price,
                percent=percent
            )
            place_laddered_take_profits(
                symbol,
                side,
                entry_price,
                tp_percents,
                percent=percent
            )
        elif direction in ["close_long", "close_short"]:
            # Close by sending reduceOnly market order in opposite direction, use same percent sizing
            side = "Sell" if direction == "close_long" else "Buy"
            open_market_position(symbol, side, percent=percent)
        else:
            return jsonify({'error': 'unknown direction'}), 400
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
