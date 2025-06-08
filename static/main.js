function fetchTotal() {
    fetch('/total')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-amount').innerText = data.total.toFixed(2) + '€';
        });
    fetchCash();
    fetchCrypto();
}

function fetchCash() {
    fetch('/cash')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cash-amount').innerText = data.cash.toFixed(2) + '€';
            renderIncomingCashList(data.incoming_cash || []);
        });
}

function fetchCrypto() {
    fetch('/crypto')
        .then(response => response.json())
        .then(data => {
            document.getElementById('crypto-amount').innerText = data.crypto.toFixed(2) + '€';
        });
}

function updateBalance() {
    changeCash(0);
}

function renderIncomingCashList(incomingCash) {
    const list = document.getElementById('incoming-cash-list');
    list.innerHTML = ''; 
    if (incomingCash.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No incoming cash entries.';
        list.appendChild(li);
        return;
    }
    incomingCash.forEach(entry => {
        const li = document.createElement('li');
        li.textContent = `${entry.amount}€ on ${entry.date}`;
        list.appendChild(li);
    });
}

function addCash() {
    const amountInput = parseFloat(document.getElementById('amount-input').value.replace(',', '.'))
    const amount = parseFloat(amountInput);
    if (!isNaN(amount)) {
        changeCash(amount);
    }
}

function removeCash() {
    const amountInput = parseFloat(document.getElementById('amount-input').value.replace(',', '.'))
    const amount = parseFloat(amountInput);
    if (!isNaN(amount)) {
        changeCash(-amount);
    }
}

function changeCash(amount) {
    fetch('/cash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('cash-amount').innerText = data.cash.toFixed(2) + '€';
        document.getElementById('crypto-amount').innerText = data.crypto.toFixed(2) + '€';
        document.getElementById('total-amount').innerText = data.total.toFixed(2) + '€';
        document.getElementById('spending-limit').innerText = data.spending_limit + '€ per day';
        renderIncomingCashList(data.incoming_cash || []);
        renderTransactionList(data.transactions || []);
    });
}

function resetBalance() {
    fetch('/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset: true })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('total-amount').innerText = data.total.toFixed(2) + '€';
        document.getElementById('cash-amount').innerText = data.cash.toFixed(2) + '€';
        document.getElementById('spending-limit').innerText = 'Loading...';
    });
} 

function addIncomingCash() {
    const amountInput = parseFloat(document.getElementById('incoming-amount').value.replace(',', '.'))
    const amount = parseFloat(amountInput);
    const date = document.getElementById('incoming-date').value
    const [year, month, day] = date.split('-');
    const formatted = `${day}.${month}.${year}`;
    if (isNaN(amount) || !date) {
        alert('Please fill in all fields correctly.');
        return;
    }
    fetch('/incoming_cash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount, date: formatted })
    })
    .then(response => response.json())
    .then(data => {
        fetchCash();
        document.getElementById('incoming-amount').value = ''
        document.getElementById('incoming-date').value = ''
    });
}

function calculateSpendingLimit() {
    const limit = parseFloat(document.getElementById('cash-amount').innerText)
    const endDateStr = document.getElementById('limit-date').value
    if (!isNaN(limit) && endDateStr) {
        const today = new Date();
        const endDate = new Date(endDateStr);
        const msPerDay = 1000 * 60 * 60 * 24;
        const daysLeft = Math.ceil((endDate - today) / msPerDay) + 1;
        if (daysLeft > 0) {
            const spendingLimit = (limit / daysLeft).toFixed(2);
            fetch('/spending_limit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: spendingLimit })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('spending-limit').innerText = `${spendingLimit}€ per day`;
            });
        } else {
            document.getElementById('spending-limit').innerText = 'Limit date has passed.';
        }
    }
}

function renderTransactionList(transactions) {
    const list = document.getElementById('transactions-list');
    list.innerHTML = ''; 
    if (transactions.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No transactions.';
        list.appendChild(li);
        return;
    }
    transactions.forEach(entry => {
        const li = document.createElement('li');
        li.innerHTML = `${entry.date}  -  <span class='amount'>${entry.amount.toFixed(2)}€</span>  -  ${entry.text}`;
        list.appendChild(li);
    });
}

function addTransaction() {
    const amountInput = parseFloat(document.getElementById('transaction-amount').value.replace(',', '.'))
    const amount = parseFloat(amountInput);
    const text = document.getElementById('transaction-text').value
    const date = document.getElementById('transaction-date').value
    if (isNaN(amount) || !text || !date) {
        alert('Please fill in all fields correctly.');
        return;
    }
    const [year, month, day] = date.split('-');
    const formatted = `${day}.${month}.${year}`;
    fetch('/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount, text: text, date: formatted })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('transaction-amount').value = ''
        document.getElementById('transaction-text').value = ''
        document.getElementById('transaction-date').value = ''
        renderTransactionList(data.transactions || []);
    });
    updateBalance();
}

document.getElementById('limit-date').addEventListener('change', calculateSpendingLimit);

window.onload = updateBalance;