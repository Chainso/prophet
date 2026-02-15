// GENERATED FILE: do not edit directly.

import { Schema, model, type Model } from 'mongoose';
import type * as Domain from './domain.js';

export interface OrderDocument extends Record<string, unknown> {
  orderId: string;
  customer: Domain.UserRef;
  totalAmount: number;
  discountCode?: string;
  tags?: string[];
  shippingAddress?: Domain.Address;
  currentState: Domain.OrderState;
}

const OrderSchema = new Schema<OrderDocument>({
  orderId: { type: String, required: true },
  customer: { type: Schema.Types.Mixed, required: true },
  totalAmount: { type: Number, required: true },
  discountCode: { type: String, required: false },
  tags: { type: [String], required: false },
  shippingAddress: { type: Schema.Types.Mixed, required: false },
  currentState: { type: String, required: true, default: 'created' },
}, { collection: 'orders', strict: false });
OrderSchema.index({ orderId: 1 }, { unique: true });
export const OrderModel: Model<OrderDocument> = model<OrderDocument>('Order', OrderSchema);

export interface UserDocument extends Record<string, unknown> {
  userId: string;
  email: string;
}

const UserSchema = new Schema<UserDocument>({
  userId: { type: String, required: true },
  email: { type: String, required: true },
}, { collection: 'users', strict: false });
UserSchema.index({ userId: 1 }, { unique: true });
export const UserModel: Model<UserDocument> = model<UserDocument>('User', UserSchema);
