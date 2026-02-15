// GENERATED FILE: do not edit directly.

import type {
  OrderRef,
  OrderState,
  UserRef
} from './domain';
import type {
  ApproveOrderResult,
  CreateOrderResult,
  ShipOrderResult
} from './actions';

export type ApproveOrderResult = ApproveOrderResult;

export type CreateOrderResult = CreateOrderResult;

export type ShipOrderResult = ShipOrderResult;

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
