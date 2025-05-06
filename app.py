from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date
from pybit.unified_trading import HTTP
from data.config import API, API_SECRET

app = Flask(__name__)
CORS(app)

cash_balance = 0
incoming_cash = []
spending_limit = 0
crypto_total = 0

session = HTTP(
    testnet=False,
    api_key=API,
    api_secret=API_SECRET,
)

@app.route('/total', methods=['GET'])
def total():
    global cash_balance, crypto_total
    total_cash = cash_balance + crypto_total
    return jsonify(total=total_cash)

@app.route('/cash', methods=['GET'])
def cash():
    return jsonify(
        cash=cash_balance,
        incoming_cash=incoming_cash,
        spending_limit=spending_limit
    )

@app.route('/crypto', methods=['GET'])
def crypto():
    global crypto_total
    crypto_total = float(session.get_wallet_balance(accountType='UNIFIED', currency='USDT')['result']['list'][0]['totalEquity'])
    return jsonify(crypto=crypto_total)


@app.route('/cash', methods=['POST'])
def update_cash():
    global cash_balance, crypto_total
    data = request.get_json()
    amount = data.get('amount', 0)
    cash_balance += amount
    if cash_balance < 0:
        cash_balance = 0
    return jsonify(cash=cash_balance, total=cash_balance + crypto_total)

@app.route('/reset', methods=['POST'])
def reset_cash():
    global cash_balance, incoming_cash, spending_limit, crypto_total
    cash_balance = 0
    total_cash = crypto_total
    incoming_cash = []
    spending_limit = 0
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
    return jsonify(incoming_cash=incoming_cash)

@app.route('/spending_limit', methods=['POST'])
def set_spending_limit():
    global spending_limit
    data = request.get_json()
    spending_limit = data.get('limit', 0)
    return jsonify(spending_limit=spending_limit)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)