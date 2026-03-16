#!/bin/bash

# QR Ordering System - Automated Setup & Run Script

echo "🚀 Starting QR Ordering System Setup..."

# 1. Backend Setup
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python3 seed.py

# Start Backend in background
echo "🟢 Starting Backend Server on http://localhost:8005..."
python3 main.py &
BACKEND_PID=$!

# 2. Frontend Setup
echo "📦 Setting up Frontend..."
cd ../frontend

# Start Frontend Server in background
echo "🟢 Starting Frontend Server on http://localhost:3000..."
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo "✅ System is up and running!"
echo "Customer Menu: http://localhost:3000/index.html"
echo "Vendor Dashboard: http://localhost:3000/vendor.html"
echo "Press Ctrl+C to stop both servers."

# Trap SIGINT to kill background processes on exit
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

# Wait for background processes
wait
