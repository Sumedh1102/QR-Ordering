from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "Pending"
    PREPARING = "Preparing"
    READY = "Ready"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"

class OrderType(str, Enum):
    DINE_IN = "Dine-in"
    TAKEAWAY = "Takeaway"

class PaymentMethod(str, Enum):
    UPI = "UPI"
    CASH = "Cash"

class MenuItemBase(BaseModel):
    name: str
    description: str
    price: float
    prep_time_minutes: int
    is_available: bool = True

class MenuItemCreate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    id: int
    vendor_id: int
    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    menu_item_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    menu_item: MenuItem
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    amount: float
    method: PaymentMethod

class PaymentCreate(PaymentBase):
    order_id: int

class Payment(PaymentBase):
    id: int
    status: PaymentStatus
    transaction_id: Optional[str] = None
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_name: str
    order_type: OrderType
    is_priority: bool = False

class OrderCreate(OrderBase):
    vendor_id: int
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    vendor_id: int
    order_number: int
    status: OrderStatus
    created_at: datetime
    estimated_ready_at: Optional[datetime] = None
    items: List[OrderItem]
    payment: Optional[Payment] = None
    
    class Config:
        from_attributes = True

class VendorBase(BaseModel):
    name: str
    email: EmailStr
    latitude: float
    longitude: float

class VendorCreate(VendorBase):
    password: str

class Vendor(VendorBase):
    id: int
    qr_code_url: Optional[str] = None
    class Config:
        from_attributes = True
