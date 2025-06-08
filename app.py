import os
import json
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import date
from pybit.unified_trading import HTTP
from pymexc import futures
from binance.um_futures import UMFutures
from data.config import API, API_SECRET, API_MEXC, API_SECRET_MEXC, API_BINANCE, API_SECRET_BINANCE

app = Flask(__name__)
CORS(app)

total_cash = 0
cash_balance = 0
incoming_cash = []
spending_limit = 0
crypto_total = 0
transactions = []

bybit_client = HTTP(testnet=False, api_key=API, api_secret=API_SECRET)

mexc_client = futures.HTTP(api_key=API_MEXC, api_secret=API_SECRET_MEXC)

binance_client = UMFutures(API_BINANCE, API_SECRET_BINANCE)

def save_data(data):
    with open('data/data.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists('data/data.json'):
        with open('data/data.json', 'r') as f:
            return json.load(f)
    else:
        return {
            'cash_balance': 0,
            'incoming_cash': [],
            'spending_limit': 0,
            'crypto_total': 0,
            'transactions': []
        }

data = load_data()
if data:
    total_cash = data["total_cash"]
    cash_balance = data["cash_balance"]
    incoming_cash = data["incoming_cash"]
    spending_limit = data["spending_limit"]
    crypto_total = data["crypto_total"]
    transactions = data["transactions"]
else:
    total_cash = 0
    cash_balance = 0
    incoming_cash = []
    spending_limit = 0
    crypto_total = 0
    transactions = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/total', methods=['GET'])
def total():
    data = load_data()
    data["total_cash"] = data["cash_balance"] + data["crypto_total"]
    save_data(data)
    return jsonify(total=data["total_cash"])

@app.route('/cash', methods=['GET'])
def cash():
    data = load_data()
    save_data(data)
    return jsonify(
        cash=data["cash_balance"],
        incoming_cash=data["incoming_cash"],
        spending_limit=data["spending_limit"]
    )

@app.route('/crypto', methods=['GET'])
def crypto():
    data = load_data()
    data["crypto_total"] = float(bybit_client.get_wallet_balance(accountType='UNIFIED', currency='USDT')['result']['list'][0]['totalEquity'])
    data["crypto_total"] += float(mexc_client.asset(currency='USDT')['data']['equity'])
    balance = binance_client.balance()
    for i in balance:
        if i['asset'] == 'BNFCR':
            data["crypto_total"] += float(i['balance'])
    
    eur_usd = float(bybit_client.get_tickers(category='spot', symbol='USDTEUR')["result"]["list"][0]["lastPrice"])
    data["crypto_total"] = round(data["crypto_total"] * eur_usd, 2)

    save_data(data)
    return jsonify(crypto=data["crypto_total"])

@app.route('/cash', methods=['POST'])
def update_cash():
    data = load_data()
    data_js = request.get_json()
    amount = data_js.get('amount', 0)
    data["cash_balance"] += amount
    
    for i in data["incoming_cash"]:
        if i["date"] == date.today().strftime('%d.%m.%Y'):
            data["cash_balance"] += i["amount"]
            data["incoming_cash"].remove(i)
    
    if data["cash_balance"] < 0:
        data["cash_balance"] = 0
    
    data["crypto_total"] = float(bybit_client.get_wallet_balance(accountType='UNIFIED', currency='USDT')['result']['list'][0]['totalEquity'])
    data["crypto_total"] += float(mexc_client.asset(currency='USDT')['data']['equity'])
    balance = binance_client.balance()
    for i in balance:
        if i['asset'] == 'BNFCR':
            data["crypto_total"] += float(i['balance'])

    eur_usd = float(bybit_client.get_tickers(category='spot', symbol='USDTEUR')["result"]["list"][0]["lastPrice"])
    data["crypto_total"] = round(data["crypto_total"] * eur_usd, 2)

    save_data(data)    
    return jsonify(cash=data["cash_balance"], crypto=data["crypto_total"], total=data["cash_balance"] + data["crypto_total"], incoming_cash=data["incoming_cash"], spending_limit=data["spending_limit"], transactions=data["transactions"])

@app.route('/reset', methods=['POST'])
def reset_cash():
    data = load_data()
    data["cash_balance"] = 0
    data["total_cash"] = data["crypto_total"]
    data["spending_limit"] = 0
    save_data(data)
    return jsonify(total=data["total_cash"], cash=data["cash_balance"], spending_limit=data["spending_limit"])

@app.route('/incoming_cash', methods=['POST'])
def add_incoming_cash():
    data = load_data()
    data_js = request.get_json()
    amount = data_js.get('amount', 0)
    date_received = data_js.get('date', date.today().strftime('%d.%m.%Y'))
    data["incoming_cash"].append({
        'amount': amount,
        'date': date_received
    })
    save_data(data)
    return jsonify(incoming_cash=data["incoming_cash"])

@app.route('/spending_limit', methods=['POST'])
def set_spending_limit():
    data = load_data()
    data_js = request.get_json()
    data["spending_limit"] = data_js.get('limit', 0)
    save_data(data)
    return jsonify(spending_limit=data["spending_limit"])

@app.route('/transactions', methods=['POST'])
def add_transaction():
    data = load_data()
    data_js = request.get_json()
    tx_amount = data_js.get('amount', 0)
    tx_text = data_js.get('text', '')
    tx_date = data_js.get('date', date.today().strftime('%d.%m.%Y'))

    data["cash_balance"] -= tx_amount
    if data["cash_balance"] < 0:
        return jsonify(error="Insufficient funds"), 400
    
    data["transactions"].insert(0, {
        'amount': tx_amount,
        'date': tx_date,
        'text': tx_text
    })
    
    save_data(data)
    return jsonify(tx_amount=tx_amount, tx_date=tx_date, tx_text=tx_text, transactions=data["transactions"], cash=data["cash_balance"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)