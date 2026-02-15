# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .domain import *

@dataclass
class ApproveOrderCommand:
    order: OrderRef
    approvedBy: Optional[UserRef] = None
    notes: Optional[List[str]] = None
    context: Optional[ApprovalContext] = None

@dataclass
class CreateOrderCommand:
    customer: UserRef
    totalAmount: float
    discountCode: Optional[str] = None
    tags: Optional[List[str]] = None
    shippingAddress: Optional[Address] = None

@dataclass
class ShipOrderCommand:
    order: OrderRef
    carrier: str
    trackingNumber: str
    packageIds: List[str]

@dataclass
class ApproveOrderResult:
    order: OrderRef
    decision: str
    warnings: Optional[List[str]] = None

@dataclass
class CreateOrderResult:
    order: OrderRef
    currentState: str

@dataclass
class ShipOrderResult:
    order: OrderRef
    shipmentStatus: str
    labels: Optional[List[str]] = None
    labelBatches: Optional[List[List[str]]] = None
