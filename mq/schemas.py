"""schemas.py"""

from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: int
    status: str


class OrderStatusResponse(BaseModel):
    order_id: int
    status: str
