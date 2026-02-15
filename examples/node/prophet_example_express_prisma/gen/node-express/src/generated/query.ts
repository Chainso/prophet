// GENERATED FILE: do not edit directly.

import type {
  OrderRef,
  OrderState,
  UserRef
} from './domain';

export interface BaseFilter<T> {
  eq?: T;
  in?: T[];
  contains?: T extends string ? string : never;
  gte?: T;
  lte?: T;
}

export interface OrderQueryFilter {
  customer?: BaseFilter<UserRef>;
  discountCode?: BaseFilter<string>;
  orderId?: BaseFilter<string>;
  totalAmount?: BaseFilter<number>;
  currentState?: BaseFilter<OrderState>;
}

export interface UserQueryFilter {
  email?: BaseFilter<string>;
  userId?: BaseFilter<string>;
}
