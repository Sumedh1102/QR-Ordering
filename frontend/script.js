


const API_BASE = "http://localhost:8005";

// Read vendor ID from QR URL
const urlParams = new URLSearchParams(window.location.search);
let currentVendorId = urlParams.get("vendor_id") || 1;
let cart = [];
let vendorLocation = { lat: 19.0760, lon: 72.8777 }; // Default from seed
let userLocation = null;
let isLocationVerified = false;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    loadVendorInfo();
    checkLocation();
    loadMenu();
});

async function loadVendorInfo() {
    try {
        const res = await fetch(`${API_BASE}/vendors/${currentVendorId}`);
        if (!res.ok) throw new Error("Vendor not found");
        const data = await res.json();
        document.getElementById('vendor-name').innerText = data.name;
        vendorLocation = { lat: data.latitude, lon: data.longitude };
    } catch (e) {
        console.error("Failed to load vendor info", e);
        document.getElementById('vendor-name').innerText = "Vendor Offline";
    }
}

function checkLocation() {
    const statusEl = document.getElementById('location-status');
    if ("geolocation" in navigator) {
        // Set a timeout for geolocation to avoid hanging
        const geoTimeout = setTimeout(() => {
            statusEl.innerText = "🚶 Location check timed out (Pre-order mode)";
        }, 5000);

        navigator.geolocation.getCurrentPosition(
            pos => {
                clearTimeout(geoTimeout);
                userLocation = { lat: pos.coords.latitude, lon: pos.coords.longitude };
                const dist = calculateDistance(userLocation.lat, userLocation.lon, vendorLocation.lat, vendorLocation.lon);

                if (dist <= 100) {
                    isLocationVerified = true;
                    statusEl.innerText = "📍 Within range of stall";
                    statusEl.classList.add('text-success');
                } else {
                    statusEl.innerText = "🚶 Distance: " + Math.round(dist) + "m (Pre-order mode)";
                }
            },
            err => {
                clearTimeout(geoTimeout);
                statusEl.innerText = "🚶 Location denied (Pre-order mode)";
                console.warn("Geolocation error:", err);
            },
            { timeout: 5000 }
        );
    } else {
        statusEl.innerText = "🚶 Geolocation not supported (Pre-order mode)";
    }
}

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // metres
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) *
        Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

async function loadMenu() {
    const grid = document.getElementById('menu-items-grid');
    grid.innerHTML = '<div class="loader" style="grid-column: 1/-1; margin: 20px auto;"></div>';

    try {
        const res = await fetch(`${API_BASE}/menu/${currentVendorId}`);
        if (!res.ok) throw new Error("Menu fetch failed");
        const items = await res.json();

        if (items.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No items available today.</p>';
            return;
        }

        grid.innerHTML = items.map(item => `
            <div class="glass-card menu-item-card">
                <h3>${item.name}</h3>
                <p class="text-muted">${item.description}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                    <span style="font-weight: 700; color: var(--primary);">₹${item.price}</span>
                    <button class="btn btn-primary" onclick="addToCart(${item.id}, '${item.name}', ${item.price})">+</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error("Failed to load menu", e);
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--danger);">Failed to load menu. Is the backend running?</p>';
    }
}

// --- Cart Logic ---
function addToCart(id, name, price) {
    const existing = cart.find(i => i.id === id);
    if (existing) {
        existing.quantity++;
    } else {
        cart.push({ id, name, price, quantity: 1 });
    }
    updateCartUI();

    // Toast notification simulation
    console.log(`Added ${name} to cart`);
}

function updateCartUI() {
    const drawer = document.getElementById('cart-drawer');
    const count = document.getElementById('cart-count');
    const total = document.getElementById('cart-total');

    const totalCount = cart.reduce((sum, i) => sum + i.quantity, 0);
    const totalPrice = cart.reduce((sum, i) => sum + (i.price * i.quantity), 0);

    if (totalCount > 0) {
        drawer.style.display = 'block';
        count.innerText = `${totalCount} Items`;
        total.innerText = `Total: ₹${totalPrice}`;
    } else {
        drawer.style.display = 'none';
    }
}

// --- View Transitions ---
function showCheckout() {
    document.getElementById('menu-view').style.display = 'none';
    document.getElementById('checkout-view').style.display = 'block';

    const list = document.getElementById('checkout-items');
    list.innerHTML = cart.map(i => `
        <div class="order-item">
            <span>${i.name} x ${i.quantity}</span>
            <span>₹${i.price * i.quantity}</span>
        </div>
    `).join('');
}

function hideCheckout() {
    document.getElementById('menu-view').style.display = 'block';
    document.getElementById('checkout-view').style.display = 'none';
}

let selectedPaymentMethod = 'UPI';
function selectPayment(method) {
    selectedPaymentMethod = method;
    document.getElementById('pay-upi').style.borderColor = method === 'UPI' ? 'var(--primary)' : 'var(--border)';
    document.getElementById('pay-cash').style.borderColor = method === 'Cash' ? 'var(--primary)' : 'var(--border)';
}

// --- Order Submission ---
async function submitOrder() {
    const name = document.getElementById('cust-name').value;
    const type = document.getElementById('order-type').value;
    const isExpress = document.getElementById('is-express').checked;

    if (!name) return alert("Please enter your name");

    const btn = document.getElementById('submit-order-btn');
    btn.disabled = true;
    btn.innerText = "Placing Order...";

    const orderData = {
        vendor_id: currentVendorId,
        customer_name: name,
        order_type: type,
        is_priority: isExpress,
        items: cart.map(i => ({ menu_item_id: i.id, quantity: i.quantity }))
    };

    try {
        const res = await fetch(`${API_BASE}/create-order/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (!res.ok) throw new Error("Order creation failed");

        const order = await res.json();

        // Create payment record
        await fetch(`${API_BASE}/payments/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                order_id: order.id,
                amount: cart.reduce((sum, i) => sum + (i.price * i.quantity), 0),
                method: selectedPaymentMethod
            })
        });

        showStatus(order);
    } catch (e) {
        alert("Failed to place order. Please try again.");
        btn.disabled = false;
        btn.innerText = "Confirm & Pay";
    }
}

function showStatus(order) {
    document.getElementById('checkout-view').style.display = 'none';
    document.getElementById('status-view').style.display = 'block';

    document.getElementById('status-order-id').innerText = `Order #${order.order_number}`;

    // Start polling for wait time
    pollQueue();
    setInterval(pollQueue, 10000); // Update every 10s
}

async function pollQueue() {
    try {
        const res = await fetch(`${API_BASE}/queue/${currentVendorId}`);
        const data = await res.json();
        document.getElementById('wait-time').innerText = `${data.estimated_wait_minutes} mins`;
        document.getElementById('queue-position').innerText = `Queue Length: ${data.queue_length} orders`;

        // Update status badge if needed (we'd need a separate endpoint for single order status normally)
    } catch (e) {
        console.error("Poll error", e);
    }
}
