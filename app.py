from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date

app = Flask(__name__)
CORS(app)

cash_balance = 0
incoming_cash = []
spending_limit = 0

@app.route('/cash', methods=['GET'])
def cash():
    return jsonify(
        cash=cash_balance,
        incoming_cash=incoming_cash,
        spending_limit=spending_limit
    )

@app.route('/cash', methods=['POST'])
def update_cash():
    global cash_balance
    data = request.get_json()
    amount = data.get('amount', 0)
    cash_balance += amount
    if cash_balance < 0:
        cash_balance = 0
    return jsonify(cash=cash_balance)

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