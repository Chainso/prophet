# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .domain import *

@dataclass
class ApproveOrderResult:
    pass

@dataclass
class CreateOrderResult:
    pass

@dataclass
class ShipOrderResult:
    pass

@dataclass
class PaymentCaptured:
    order: OrderRef

@dataclass
class OrderApproveTransition:
    pass

@dataclass
class OrderShipTransition:
    pass
