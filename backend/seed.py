from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # 1. Create a Vendor
    vendor = models.Vendor(
        name="Street Bites - Momos & More",
        email="vendor@example.com",
        hashed_password="password123", # In real app, use hashing
        latitude=19.0760, # Example: Mumbai lat
        longitude=72.8777, # Example: Mumbai lon
        qr_code_url="http://localhost:8005/vendor/1"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    # 2. Add Menu Items
    items = [
        models.MenuItem(vendor_id=vendor.id, name="Veg Steam Momos", description="6 pieces with spicy chutney", price=80.0, prep_time_minutes=5),
        models.MenuItem(vendor_id=vendor.id, name="Paneer Momos", description="6 pieces with creamy dip", price=100.0, prep_time_minutes=7),
        models.MenuItem(vendor_id=vendor.id, name="Chicken Momos", description="6 pieces, authentic taste", price=120.0, prep_time_minutes=6),
        models.MenuItem(vendor_id=vendor.id, name="Classic Cold Coffee", description="Refreshing and creamy", price=60.0, prep_time_minutes=3),
    ]
    db.add_all(items)
    db.commit()
    print(f"Seed complete. Vendor ID: {vendor.id}")
    db.close()

if __name__ == "__main__":
    seed()
