import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date
from pybit.unified_trading import HTTP
from pymexc import futures
from binance.um_futures import UMFutures
from data.config import API, API_SECRET, API_MEXC, API_SECRET_MEXC, API_BINANCE, API_SECRET_BINANCE

app = Flask(__name__)
CORS(app)

cash_balance = 0
incoming_cash = []
spending_limit = 0
crypto_total = 0

bybit_client = HTTP(testnet=False, api_key=API, api_secret=API_SECRET)

mexc_client = futures.HTTP(api_key=API_MEXC, api_secret=API_SECRET_MEXC)

binance_client = UMFutures(API_BINANCE, API_SECRET_BINANCE)

def save_data():
    global cash_balance, incoming_cash, spending_limit, crypto_total
    with open('data/data.json', 'w') as f:
        json.dump({
            'cash_balance': cash_balance,
            'incoming_cash': incoming_cash,
            'spending_limit': spending_limit,
            'crypto_total': crypto_total
        }, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists('data/data.json'):
        with open('data/data.json', 'r') as f:
            return json.load(f)

@app.route('/total', methods=['GET'])
def total():
    global cash_balance, crypto_total
    total_cash = cash_balance + crypto_total
    save_data()
    return jsonify(total=total_cash)

@app.route('/cash', methods=['GET'])
def cash():
    save_data()
    return jsonify(
        cash=cash_balance,
        incoming_cash=incoming_cash,
        spending_limit=spending_limit
    )

@app.route('/crypto', methods=['GET'])
def crypto():
    global crypto_total
    crypto_total = float(bybit_client.get_wallet_balance(accountType='UNIFIED', currency='USDT')['result']['list'][0]['totalEquity'])
    crypto_total += float(mexc_client.asset(currency='USDT')['data']['equity'])
    balance = binance_client.balance()
    for i in balance:
        if i['asset'] == 'BNFCR':
            crypto_total += float(i['balance'])
    save_data()
    return jsonify(crypto=crypto_total)


@app.route('/cash', methods=['POST'])
def update_cash():
    global cash_balance, crypto_total
    data = request.get_json()
    amount = data.get('amount', 0)
    cash_balance += amount
    if cash_balance < 0:
        cash_balance = 0
    save_data()    
    return jsonify(cash=cash_balance, total=cash_balance + crypto_total)

@app.route('/reset', methods=['POST'])
def reset_cash():
    global cash_balance, incoming_cash, spending_limit, crypto_total
    cash_balance = 0
    total_cash = crypto_total
    incoming_cash = []
    spending_limit = 0
    save_data()
    return jsonify(total=total_cash, cash=cash_balance, incoming_cash=incoming_cash, spending_limit=spending_limit)

@app.route('/incoming_cash', methods=['POST'])
def add_incoming_cash():
    global incoming_cash
    data = request.get_json()
    amount = data.get('amount', 0)
    date_received = data.get('date', date.today().isoformat())
    incoming_cash.append({
        'amount': amount,
        'date': date_received
    })
    save_data()
    return jsonify(incoming_cash=incoming_cash)

@app.route('/spending_limit', methods=['POST'])
def set_spending_limit():
    global spending_limit
    data = request.get_json()
    spending_limit = data.get('limit', 0)
    save_data()
    return jsonify(spending_limit=spending_limit)


if __name__ == '__main__':
    data = load_data()
    if data:
        cash_balance = data["cash_balance"]
        incoming_cash = data["incoming_cash"]
        spending_limit = data["spending_limit"]
        crypto_total = data["crypto_total"]
    else:
        cash_balance = 0
        incoming_cash = []
        spending_limit = 0
        crypto_total = 0

    app.run(host='0.0.0.0', port=5000)