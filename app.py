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
transactions = []

bybit_client = HTTP(testnet=False, api_key=API, api_secret=API_SECRET)

mexc_client = futures.HTTP(api_key=API_MEXC, api_secret=API_SECRET_MEXC)

binance_client = UMFutures(API_BINANCE, API_SECRET_BINANCE)

def save_data():
    global cash_balance, incoming_cash, spending_limit, crypto_total, transactions
    with open('data/data.json', 'w') as f:
        json.dump({
            'cash_balance': cash_balance,
            'incoming_cash': incoming_cash,
            'spending_limit': spending_limit,
            'crypto_total': crypto_total,
            'transactions': transactions
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
    
    eur_usd = float(bybit_client.get_tickers(category='spot', symbol='USDTEUR')["result"]["list"][0]["lastPrice"])
    crypto_total = round(crypto_total * eur_usd, 2)

    save_data()
    return jsonify(crypto=crypto_total)

@app.route('/cash', methods=['POST'])
def update_cash():
    global cash_balance, crypto_total, incoming_cash, spending_limit, transactions
    data = request.get_json()
    amount = data.get('amount', 0)
    cash_balance += amount
    
    for i in incoming_cash:
        if i["date"] == date.today().strftime('%d.%m.%Y'):
            cash_balance += i["amount"]
            incoming_cash.remove(i)
    
    if cash_balance < 0:
        cash_balance = 0
    
    crypto_total = float(bybit_client.get_wallet_balance(accountType='UNIFIED', currency='USDT')['result']['list'][0]['totalEquity'])
    crypto_total += float(mexc_client.asset(currency='USDT')['data']['equity'])
    balance = binance_client.balance()
    for i in balance:
        if i['asset'] == 'BNFCR':
            crypto_total += float(i['balance'])

    eur_usd = float(bybit_client.get_tickers(category='spot', symbol='USDTEUR')["result"]["list"][0]["lastPrice"])
    crypto_total = round(crypto_total * eur_usd, 2)

    save_data()    
    return jsonify(cash=cash_balance, crypto=crypto_total, total=cash_balance + crypto_total, incoming_cash=incoming_cash, spending_limit=spending_limit, transactions=transactions)

@app.route('/reset', methods=['POST'])
def reset_cash():
    global cash_balance, incoming_cash, spending_limit, crypto_total
    cash_balance = 0
    total_cash = crypto_total
    spending_limit = 0
    save_data()
    return jsonify(total=total_cash, cash=cash_balance, spending_limit=spending_limit)

@app.route('/incoming_cash', methods=['POST'])
def add_incoming_cash():
    global incoming_cash
    data = request.get_json()
    amount = data.get('amount', 0)
    date_received = data.get('date', date.today().strftime('%d.%m.%Y'))
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

@app.route('/transactions', methods=['POST'])
def add_transaction():
    global cash_balance, transactions
    data = request.get_json()
    tx_amount = data.get('amount', 0)
    tx_date = date.today().strftime('%d.%m.%Y')
    tx_text = data.get('text', '')

    cash_balance -= tx_amount
    if cash_balance < 0:
        return jsonify(error="Insufficient funds"), 400
    
    transactions.insert(0, {
        'amount': tx_amount,
        'date': tx_date,
        'text': tx_text
    })
    
    save_data()
    return jsonify(tx_amount=tx_amount, tx_date=tx_date, tx_text=tx_text, transactions=transactions, cash=cash_balance)


if __name__ == '__main__':
    data = load_data()
    if data:
        cash_balance = data["cash_balance"]
        incoming_cash = data["incoming_cash"]
        spending_limit = data["spending_limit"]
        crypto_total = data["crypto_total"]
        transactions = data["transactions"]
    else:
        cash_balance = 0
        incoming_cash = []
        spending_limit = 0
        crypto_total = 0
        transactions = []

    app.run(host='0.0.0.0', port=5000)