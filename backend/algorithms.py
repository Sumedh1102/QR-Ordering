
from datetime import datetime, timedelta
from typing import List
from models import Order, OrderStatus

def calculate_estimated_wait_time(orders_in_queue: List[Order]) -> int:
    """
    Calculates total estimated wait time based on orders currently being prepared or pending.
    Sum of prep times for all active items in the queue.
    """
    total_wait_minutes = 0
    for order in orders_in_queue:
        if order.status in [OrderStatus.PENDING, OrderStatus.PREPARING]:
            for item in order.items:
                total_wait_minutes += item.menu_item.prep_time_minutes * item.quantity
    return total_wait_minutes

def schedule_orders(orders: List[Order]) -> List[Order]:
    """
    Schedules orders based on OS concepts:
    - Priority Queue: Express/Small orders go first
    - FCFS: Within same priority level, earliest order goes first
    
    Rule: Small order (<= 2 items total) or marked as 'Express' gets priority.
    """
    def get_priority(order: Order):
        total_items = sum(item.quantity for item in order.items)
        # Priority 0 (highest) if small order or explicit priority
        # Priority 1 (normal) otherwise
        is_small = total_items <= 2
        return 0 if (order.is_priority or is_small) else 1

    # Sort by priority first, then by creation time (FCFS)
    # Lower number = higher priority
    scheduled = sorted(orders, key=lambda x: (get_priority(x), x.created_at))
    return scheduled

def update_queue_estimates(orders: List[Order]):
    """
    Sets estimated_ready_at for each order in the queue based on sequence.
    """
    current_time = datetime.utcnow()
    cumulative_wait = 0
    
    # We only estimate for Pending/Preparing orders
    queue = [o for o in orders if o.status in [OrderStatus.PENDING, OrderStatus.PREPARING]]
    scheduled_queue = schedule_orders(queue)
    
    for order in scheduled_queue:
        order_prep_time = sum(item.menu_item.prep_time_minutes * item.quantity for item in order.items)
        cumulative_wait += order_prep_time
        order.estimated_ready_at = current_time + timedelta(minutes=cumulative_wait)
    
    return scheduled_queue
