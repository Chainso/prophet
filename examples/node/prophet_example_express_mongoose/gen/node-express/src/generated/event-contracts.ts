// GENERATED FILE: do not edit directly.

import type {
  OrderRef,
  UserRef
} from './domain.js';
import type {
  ApproveOrderResult as ApproveOrderResultActionOutput,
  CreateOrderResult as CreateOrderResultActionOutput,
  ShipOrderResult as ShipOrderResultActionOutput
} from './actions.js';

export type ApproveOrderResult = ApproveOrderResultActionOutput;

export type CreateOrderResult = CreateOrderResultActionOutput;

export type ShipOrderResult = ShipOrderResultActionOutput;

export interface PaymentCaptured {
  order: OrderRef;
}

export interface OrderApproveTransition {
  object: OrderRef;
}

export interface OrderShipTransition {
  object: OrderRef;
}
