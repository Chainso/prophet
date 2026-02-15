# GENERATED FILE: do not edit directly.
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

class OrderModel(SQLModel, table=True):
    __tablename__ = 'orders'
    orderId: str = Field(primary_key=True)
    customer: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=false, primary_key=False))
    totalAmount: float = Field(primary_key=False)
    discountCode: Optional[str] = Field(default=None, primary_key=False)
    tags: Optional[list] = Field(default=None, sa_column=Column(JSON, nullable=true, primary_key=False))
    shippingAddress: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=true, primary_key=False))
    currentState: str = Field(default='created')

class UserModel(SQLModel, table=True):
    __tablename__ = 'users'
    userId: str = Field(primary_key=True)
    email: str = Field(primary_key=False)
