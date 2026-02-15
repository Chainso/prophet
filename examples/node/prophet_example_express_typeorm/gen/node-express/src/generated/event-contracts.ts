// GENERATED FILE: do not edit directly.

import type {
  OrderRef,
  OrderState,
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
  fromState: OrderState;
  toState: OrderState;
}

export interface OrderShipTransition {
  object: OrderRef;
  fromState: OrderState;
  toState: OrderState;
}
