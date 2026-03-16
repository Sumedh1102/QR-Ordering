# How to Run the QR Ordering System

### 1. Prerequisites
- Python 3.8+
- Node.js (for simple http server) or any static file server

### 2. Backend Setup
```powershell
cd backend
pip install -r requirements.txt
python seed.py
python main.py
```
The backend will run at `http://localhost:8000`.

### 3. Frontend Setup
You need a simple web server to serve the frontend files (to avoid CORS/file issues).
```powershell
cd frontend
# Using Python's built-in server
python -m http.server 3000
```
- Customer Menu: `http://localhost:3000/index.html`
- Vendor Dashboard: `http://localhost:3000/vendor.html`

### 4. Features to Test
1. **Geolocation**: The app will request your location. It calculates distance from the vendor (Mumbai coordinate in seed).
2. **Scheduling**: FCFS is default. Mark an order as "isExpress" or keep it small (<= 2 items) to see it jump ahead in the vendor queue.
3. **Real-time**: Vendor dashboard polls every 5 seconds for new orders.
4. **Wait Time**: Calculated dynamically based on the prep time of all items in the current queue.
