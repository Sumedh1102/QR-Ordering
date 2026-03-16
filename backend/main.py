from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import models, schemas, database, algorithms
from database import engine, get_db
from datetime import datetime
import qrcode
import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="QR Ordering System API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

@app.get("/debug-files")
async def debug_files():
    try:
        files = os.listdir(FRONTEND_DIR)
        return {"frontend_dir": FRONTEND_DIR, "files": files}
    except Exception as e:
        return {"error": str(e), "path": FRONTEND_DIR}

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# --- Vendor Endpoints ---

# --- Vendor Endpoints ---

@app.post("/vendors/", response_model=schemas.Vendor)
def create_vendor(vendor: schemas.VendorCreate, request: Request, db: Session = Depends(get_db)):
    base_url = str(request.base_url)
    db_vendor = models.Vendor(
        name=vendor.name,
        email=vendor.email,
        hashed_password=vendor.password, # In real app, hash this
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        qr_code_url=f"{base_url}frontend/index.html?vendor_id=1" # Simplified for this demo
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

# --- Menu Endpoints ---

@app.post("/menu-items/", response_model=schemas.MenuItem)
def create_menu_item(item: schemas.MenuItemCreate, vendor_id: int, db: Session = Depends(get_db)):
    db_item = models.MenuItem(**item.dict(), vendor_id=vendor_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/menu/{vendor_id}", response_model=List[schemas.MenuItem])
def get_menu(vendor_id: int, db: Session = Depends(get_db)):
    return db.query(models.MenuItem).filter(models.MenuItem.vendor_id == vendor_id).all()

# --- Order Endpoints ---

@app.post("/create-order/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    # 1. Get latest order number for this vendor today
    today = datetime.utcnow().date()
    last_order = db.query(models.Order).filter(
        models.Order.vendor_id == order.vendor_id,
        models.Order.created_at >= datetime(today.year, today.month, today.day)
    ).order_by(models.Order.order_number.desc()).first()
    
    order_number = (last_order.order_number + 1) if last_order else 1
    
    # 2. Create Order
    db_order = models.Order(
        vendor_id=order.vendor_id,
        customer_name=order.customer_name,
        order_number=order_number,
        order_type=order.order_type,
        is_priority=order.is_priority
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # 3. Create Order Items
    for item in order.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    
    # 4. Trigger Queue Estimation Update
    all_active_orders = db.query(models.Order).filter(
        models.Order.vendor_id == order.vendor_id,
        models.Order.status.in_([models.OrderStatus.PENDING, models.OrderStatus.PREPARING])
    ).all()
    
    algorithms.update_queue_estimates(all_active_orders)
    db.commit()
    
    return db_order

@app.get("/orders/{vendor_id}", response_model=List[schemas.Order])
def get_vendor_orders(vendor_id: int, status: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Order).filter(models.Order.vendor_id == vendor_id)
    if status:
        query = query.filter(models.Order.status == status)
    
    orders = query.all()
    # Sort them using our algorithm for display
    return algorithms.schedule_orders(orders)

@app.patch("/update-order-status/{order_id}/", response_model=schemas.Order)
def update_order_status(order_id: int, status: schemas.OrderStatus, db: Session = Depends(get_db)):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db_order.status = status
    db.commit()
    
    # Re-calculate estimates for all remaining orders in queue
    all_active_orders = db.query(models.Order).filter(
        models.Order.vendor_id == db_order.vendor_id,
        models.Order.status.in_([models.OrderStatus.PENDING, models.OrderStatus.PREPARING])
    ).all()
    
    algorithms.update_queue_estimates(all_active_orders)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/queue/{vendor_id}")
def get_queue_status(vendor_id: int, db: Session = Depends(get_db)):
    active_orders = db.query(models.Order).filter(
        models.Order.vendor_id == vendor_id,
        models.Order.status.in_([models.OrderStatus.PENDING, models.OrderStatus.PREPARING])
    ).all()
    
    scheduled = algorithms.schedule_orders(active_orders)
    wait_time = algorithms.calculate_estimated_wait_time(active_orders)
    
    return {
        "queue_length": len(scheduled),
        "estimated_wait_minutes": wait_time,
        "next_orders": [o.order_number for o in scheduled[:5]]
    }

@app.post("/payments/", response_model=schemas.Payment)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    db_payment = models.Payment(
        order_id=payment.order_id,
        amount=payment.amount,
        method=payment.method,
        status=models.PaymentStatus.COMPLETED # Simulation logic
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/style.css")
async def read_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))

@app.get("/script.js")
async def read_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))

@app.get("/vendor_script.js")
async def read_vendor_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "vendor_script.js"))

@app.get("/vendor")
async def read_vendor():
    return FileResponse(os.path.join(FRONTEND_DIR, "vendor.html"))

# Final fallback: Serve images and other static assets
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
