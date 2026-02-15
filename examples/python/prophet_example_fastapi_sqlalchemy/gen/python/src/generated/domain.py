# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

Money = float

@dataclass
class OrderRef:
    orderId: str

@dataclass
class UserRef:
    userId: str

@dataclass
class Address:
    line1: str
    city: str
    countryCode: str

@dataclass
class ApprovalContext:
    approver: UserRef
    watchers: Optional[List[UserRef]] = None
    reason: Optional[str] = None

OrderState = Literal['created', 'approved', 'shipped']

@dataclass
class Order:
    orderId: str
    customer: UserRef
    totalAmount: float
    discountCode: Optional[str] = None
    tags: Optional[List[str]] = None
    shippingAddress: Optional[Address] = None
    currentState: OrderState

@dataclass
class User:
    userId: str
    email: str
