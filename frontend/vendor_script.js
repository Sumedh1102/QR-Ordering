const API_BASE = "http://localhost:8005";
let currentVendorId = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadVendorOrders();
    loadVendorMenu();
    setInterval(loadVendorOrders, 5000); // Polling every 5s
});

function showSection(section) {
    document.getElementById('orders-section').style.display = section === 'orders' ? 'grid' : 'none';
    document.getElementById('menu-section').style.display = section === 'menu' ? 'block' : 'none';
}

// --- Order Management ---
async function loadVendorOrders() {
    try {
        const res = await fetch(`${API_BASE}/orders/${currentVendorId}`);
        const orders = await res.json();

        renderQueueList(orders);
        renderOrderCards(orders);
        updateStats(orders);
    } catch (e) {
        console.error("Failed to load orders", e);
    }
}

function renderQueueList(orders) {
    const list = document.getElementById('queue-list');
    const active = orders.filter(o => o.status === 'Pending' || o.status === 'Preparing');

    list.innerHTML = active.map(o => `
        <div style="background: var(--glass); padding: 10px; border-radius: 8px; text-align: center;">
            <div style="font-size: 1.2rem; font-weight: 700;">#${o.order_number}</div>
            <div class="text-muted" style="font-size: 0.7rem;">${o.customer_name}</div>
        </div>
    `).join('');
}

function renderOrderCards(orders) {
    const container = document.getElementById('orders-container');
    container.innerHTML = orders.map(o => {
        const statusClass = `badge-${o.status.toLowerCase()}`;
        return `
            <div class="glass-card" style="margin-bottom: 15px; border-left: 4px solid var(--primary);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3>Order #${o.order_number} (${o.customer_name})</h3>
                        <p class="text-muted">${o.order_type} | ${o.is_priority ? '⚡ Express' : 'Normal'}</p>
                    </div>
                    <span class="badge ${statusClass}">${o.status}</span>
                </div>
                
                <div style="margin: 15px 0;">
                    ${o.items.map(i => `<div>${i.quantity}x ${i.menu_item.name}</div>`).join('')}
                </div>

                <div style="display: flex; gap: 10px;">
                    ${o.status === 'Pending' ? `<button class="btn btn-primary" onclick="updateStatus(${o.id}, 'Preparing')">Start Preparing</button>` : ''}
                    ${o.status === 'Preparing' ? `<button class="btn btn-primary" style="background: var(--success);" onclick="updateStatus(${o.id}, 'Ready')">Mark Ready</button>` : ''}
                    ${o.status === 'Ready' ? `<button class="btn" style="background: var(--glass);" onclick="updateStatus(${o.id}, 'Completed')">Complete</button>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

async function updateStatus(orderId, status) {
    await fetch(`${API_BASE}/update-order-status/${orderId}/?status=${status}`, {
        method: 'PATCH'
    });
    loadVendorOrders();
}

function updateStats(orders) {
    const active = orders.filter(o => o.status === 'Pending' || o.status === 'Preparing').length;
    document.getElementById('queue-stats').innerText = `Queue: ${active} | Live Status: Active`;
}

// --- Menu Management ---
async function loadVendorMenu() {
    try {
        const res = await fetch(`${API_BASE}/menu/${currentVendorId}`);
        const items = await res.json();
        const list = document.getElementById('vendor-menu-list');

        list.innerHTML = items.map(item => `
            <div class="order-item">
                <div>
                    <strong>${item.name}</strong> - ₹${item.price}
                    <div class="text-muted" style="font-size: 0.8rem;">${item.prep_time_minutes} mins prep</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error("Failed to load menu", e);
    }
}

async function addMenuItem() {
    const name = document.getElementById('new-item-name').value;
    const price = document.getElementById('new-item-price').value;
    const prep = document.getElementById('new-item-prep').value;
    const desc = document.getElementById('new-item-desc').value;

    if (!name || !price || !prep) return alert("Please fill all required fields");

    const itemData = {
        name,
        price: parseFloat(price),
        prep_time_minutes: parseInt(prep),
        description: desc,
        is_available: true
    };

    try {
        const res = await fetch(`${API_BASE}/menu-items/?vendor_id=${currentVendorId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(itemData)
        });

        if (res.ok) {
            alert("Item added successfully!");
            document.getElementById('new-item-name').value = '';
            document.getElementById('new-item-price').value = '';
            document.getElementById('new-item-prep').value = '';
            document.getElementById('new-item-desc').value = '';
            loadVendorMenu();
        }
    } catch (e) {
        alert("Failed to add item.");
    }
}
