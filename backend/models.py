from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "Pending"
    PREPARING = "Preparing"
    READY = "Ready"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    qr_code_url = Column(String) # Link to vendor menu

class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    prep_time_minutes = Column(Integer) # Average prep time
    is_available = Column(Boolean, default=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    customer_name = Column(String)
    order_number = Column(Integer) # Queue number for the day
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    order_type = Column(String) # "Dine-in" or "Takeaway"
    is_priority = Column(Boolean, default=False) # Express/Small order priority
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    estimated_ready_at = Column(DateTime)
    
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer)
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float)
    method = Column(String) # "UPI" or "Cash"
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)
    
    order = relationship("Order", back_populates="payment")
