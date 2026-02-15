# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .domain import *

@dataclass
class OrderCurrentStateFilter:
    eq: Optional[str] = None
    inValues: Optional[List[str]] = None

@dataclass
class OrderCustomerFilter:
    eq: Optional[UserRef] = None
    inValues: Optional[List[UserRef]] = None

@dataclass
class OrderDiscountCodeFilter:
    eq: Optional[str] = None
    inValues: Optional[List[str]] = None
    contains: Optional[str] = None

@dataclass
class OrderOrderIdFilter:
    eq: Optional[str] = None
    inValues: Optional[List[str]] = None
    contains: Optional[str] = None

@dataclass
class OrderTotalAmountFilter:
    eq: Optional[float] = None
    inValues: Optional[List[float]] = None
    gte: Optional[float] = None
    lte: Optional[float] = None

@dataclass
class OrderQueryFilter:
    currentState: Optional[OrderCurrentStateFilter] = None
    customer: Optional[OrderCustomerFilter] = None
    discountCode: Optional[OrderDiscountCodeFilter] = None
    orderId: Optional[OrderOrderIdFilter] = None
    totalAmount: Optional[OrderTotalAmountFilter] = None

@dataclass
class UserEmailFilter:
    eq: Optional[str] = None
    inValues: Optional[List[str]] = None
    contains: Optional[str] = None

@dataclass
class UserUserIdFilter:
    eq: Optional[str] = None
    inValues: Optional[List[str]] = None
    contains: Optional[str] = None

@dataclass
class UserQueryFilter:
    email: Optional[UserEmailFilter] = None
    userId: Optional[UserUserIdFilter] = None
