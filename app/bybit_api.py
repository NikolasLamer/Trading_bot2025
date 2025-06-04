import time, hmac, hashlib, requests
from urllib.parse import urlencode
from .config import BYBIT_API_KEY, BYBIT_API_SECRET

BASE_URL = "https://api.bybit.com"

def sign_payload(payload):
    return hmac.new(
        BYBIT_API_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def bybit_request(method, path, params=None, is_private=False):
    url = BASE_URL + path
    headers = {}
    if params is None:
        params = {}

    if is_private:
        ts = str(int(time.time() * 1000))
        recv_window = "5000"
        param_str = urlencode(sorted(params.items()))
        sign_str = BYBIT_API_KEY + ts + recv_window + param_str
        signature = sign_payload(sign_str)
        headers = {
            "X-BAPI-API-KEY": BYBIT_API_KEY,
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json"
        }
    if method.upper() == "GET":
        resp = requests.get(url, params=params, headers=headers, timeout=10)
    else:
        resp = requests.post(url, json=params, headers=headers, timeout=10)
    resp.raise_for_status()
    res = resp.json()
    if res.get("retCode", 0) != 0:
        raise Exception(f"Bybit Error: {res.get('retMsg', 'Unknown')}")
    return res
