// GENERATED FILE: do not edit directly.

import type {
  OrderRef,
  OrderState,
  UserRef
} from './domain.js';

export interface OrderQueryFilter {
  customer?: {
    eq?: UserRef;
    in?: UserRef[];
  };
  discountCode?: {
    eq?: string;
    in?: string[];
    contains?: string;
  };
  orderId?: {
    eq?: string;
    in?: string[];
    contains?: string;
  };
  totalAmount?: {
    eq?: number;
    in?: number[];
    gte?: number;
    lte?: number;
  };
  currentState?: {
    eq?: OrderState;
    in?: OrderState[];
  };
}

export interface UserQueryFilter {
  email?: {
    eq?: string;
    in?: string[];
    contains?: string;
  };
  userId?: {
    eq?: string;
    in?: string[];
    contains?: string;
  };
}
