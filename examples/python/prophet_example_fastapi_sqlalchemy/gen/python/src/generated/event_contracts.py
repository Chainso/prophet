# GENERATED FILE: do not edit directly.
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from .domain import *

@dataclass(kw_only=True)
class ApproveOrderResult:
    pass

@dataclass(kw_only=True)
class CreateOrderResult:
    pass

@dataclass(kw_only=True)
class ShipOrderResult:
    pass

@dataclass(kw_only=True)
class PaymentCaptured:
    order: OrderRef

@dataclass(kw_only=True)
class OrderApproveTransition:
    pass

@dataclass(kw_only=True)
class OrderShipTransition:
    pass
