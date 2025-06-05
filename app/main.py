from flask import Flask, request, jsonify
import logging
from trade import verify_passphrase, execute_trade

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    ticker = data.get('ticker')
    direction = data.get('direction')
    passphrase = data.get('passphrase')

    if not verify_passphrase(passphrase):
        return jsonify({'error': 'Unauthorized'}), 403

    if direction not in ['OpenLong', 'OpenShort']:
        return jsonify({'error': 'Invalid direction'}), 400

    try:
        execute_trade(ticker, direction)
        return jsonify({'status': 'Trade executed successfully'}), 200
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return jsonify({'error': 'Trade execution failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
