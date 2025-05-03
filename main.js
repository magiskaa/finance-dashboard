function fetchCash() {
    fetch('http://localhost:5000/cash')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cash-amount').innerText = data.cash;
            renderIncomingCashList(data.incoming_cash || []);
        });
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
    const amount = parseFloat(document.getElementById('amount-input').value)
    if (!isNaN(amount)) {
        changeCash(amount);
    }
}

function removeCash() {
    const amount = parseFloat(document.getElementById('amount-input').value)
    if (!isNaN(amount)) {
        changeCash(-amount);
    }
}

function changeCash(amount) {
    fetch('http://localhost:5000/cash', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('cash-amount').innerText = data.cash
    });
}

function addIncomingCash() {
    const amount = parseFloat(document.getElementById('incoming-amount').value)
    const date = document.getElementById('incoming-date').value
    if (!isNaN(amount) && date) {
        fetch('http://localhost:5000/incoming_cash', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount, date: date })
        })
        .then(response => response.json())
        .then(data => {
            fetchCash();
            document.getElementById('incoming-amount').value = ''
            document.getElementById('incoming-date').value = ''
        });
    }
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
            document.getElementById('spending-limit').innerText = `${spendingLimit}€ per day`;
        } else {
            document.getElementById('spending-limit').innerText = 'Limit date has passed.';
        }
    }
}

document.getElementById('limit-date').addEventListener('change', calculateSpendingLimit);

window.onload = fetchCash