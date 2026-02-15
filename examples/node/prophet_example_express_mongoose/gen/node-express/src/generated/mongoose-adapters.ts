// GENERATED FILE: do not edit directly.

import type { FilterQuery, Model } from 'mongoose';
import type * as Domain from './domain.js';
import type * as Filters from './query.js';
import type * as Persistence from './persistence.js';
import {
  OrderModel,
  UserModel
} from './mongoose-models.js';
import type {
  OrderDocument,
  UserDocument
} from './mongoose-models.js';

function normalizePage(page: number, size: number): { page: number; size: number } {
  const normalizedPage = Number.isFinite(page) && page >= 0 ? Math.trunc(page) : 0;
  const normalizedSize = Number.isFinite(size) && size > 0 ? Math.trunc(size) : 20;
  return { page: normalizedPage, size: normalizedSize };
}

function totalPages(totalElements: number, size: number): number {
  if (size <= 0) return 0;
  return Math.ceil(totalElements / size);
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export interface MongooseGeneratedModels {
  order?: Model<OrderDocument>;
  user?: Model<UserDocument>;
}

export class MongooseGeneratedRepositories implements Persistence.GeneratedRepositories {
  order: Persistence.OrderRepository;
  user: Persistence.UserRepository;

  constructor(models: MongooseGeneratedModels = {}) {
    this.order = new OrderMongooseRepository(models.order ?? OrderModel);
    this.user = new UserMongooseRepository(models.user ?? UserModel);
  }
}

function orderWhere(filter: Filters.OrderQueryFilter | undefined): FilterQuery<OrderDocument> {
  if (!filter) return {};
  const and: Record<string, unknown>[] = [];
  const customerFilter = filter.customer;
  if (customerFilter?.eq !== undefined) {
    and.push({ 'customer.userId': customerFilter.eq.userId });
  }
  if (customerFilter?.in?.length) {
    and.push({
      $or: customerFilter.in.map((entry: any) => ({
        'customer.userId': entry.userId,
      })),
    });
  }
  const discountCodeFilter = filter.discountCode;
  if (discountCodeFilter?.eq !== undefined) and.push({ discountCode: discountCodeFilter.eq });
  if (discountCodeFilter?.in?.length) and.push({ discountCode: { $in: discountCodeFilter.in } });
  if (typeof discountCodeFilter?.contains === 'string' && discountCodeFilter.contains.length > 0) and.push({ discountCode: { $regex: escapeRegex(discountCodeFilter.contains), $options: 'i' } });
  const orderIdFilter = filter.orderId;
  if (orderIdFilter?.eq !== undefined) and.push({ orderId: orderIdFilter.eq });
  if (orderIdFilter?.in?.length) and.push({ orderId: { $in: orderIdFilter.in } });
  if (typeof orderIdFilter?.contains === 'string' && orderIdFilter.contains.length > 0) and.push({ orderId: { $regex: escapeRegex(orderIdFilter.contains), $options: 'i' } });
  const totalAmountFilter = filter.totalAmount;
  if (totalAmountFilter?.eq !== undefined) and.push({ totalAmount: totalAmountFilter.eq });
  if (totalAmountFilter?.in?.length) and.push({ totalAmount: { $in: totalAmountFilter.in } });
  if (totalAmountFilter?.gte !== undefined) and.push({ totalAmount: { $gte: totalAmountFilter.gte } });
  if (totalAmountFilter?.lte !== undefined) and.push({ totalAmount: { $lte: totalAmountFilter.lte } });
  const currentStateFilter = filter.currentState;
  if (currentStateFilter?.eq !== undefined) and.push({ currentState: currentStateFilter.eq });
  if (currentStateFilter?.in?.length) and.push({ currentState: { $in: currentStateFilter.in } });
  if (and.length === 0) return {};
  return { $and: and };
}

function orderIdFromDomain(item: Domain.Order): Persistence.OrderId {
  return {
    orderId: item.orderId,
  };
}

function orderPrimaryFilter(id: Persistence.OrderId): Record<string, unknown> {
  return {
    orderId: id.orderId,
  };
}

function orderSort(): Record<string, 1> {
  return {
    orderId: 1,
  };
}

function orderDocumentToDomain(doc: any): Domain.Order {
  return {
    orderId: doc.orderId,
    customer: doc.customer,
    totalAmount: doc.totalAmount,
    discountCode: doc.discountCode ?? undefined,
    tags: doc.tags ?? undefined,
    shippingAddress: doc.shippingAddress ?? undefined,
    currentState: doc.currentState,
  };
}

function orderDomainToDocument(item: Domain.Order): Record<string, unknown> {
  return {
    orderId: item.orderId,
    customer: item.customer,
    totalAmount: item.totalAmount,
    discountCode: item.discountCode ?? null,
    tags: item.tags ?? null,
    shippingAddress: item.shippingAddress ?? null,
    currentState: item.currentState,
  };
}

class OrderMongooseRepository implements Persistence.OrderRepository {
  constructor(private readonly model: Model<OrderDocument>) {}

  async list(page: number, size: number): Promise<Persistence.Page<Domain.Order>> {
    const normalized = normalizePage(page, size);
    const [rows, totalElements] = await Promise.all([
      this.model.find({}).sort(orderSort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),
      this.model.countDocuments({}).exec(),
    ]);
    return {
      items: rows.map(orderDocumentToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async getById(id: Persistence.OrderId): Promise<Domain.Order | null> {
    const row = await this.model.findOne(orderPrimaryFilter(id)).lean().exec();
    return row ? orderDocumentToDomain(row) : null;
  }

  async query(filter: Filters.OrderQueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.Order>> {
    const normalized = normalizePage(page, size);
    const where = orderWhere(filter);
    const [rows, totalElements] = await Promise.all([
      this.model.find(where).sort(orderSort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),
      this.model.countDocuments(where).exec(),
    ]);
    return {
      items: rows.map(orderDocumentToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async save(item: Domain.Order): Promise<Domain.Order> {
    const id = orderIdFromDomain(item);
    const payload = orderDomainToDocument(item);
    const persisted = await this.model.findOneAndUpdate(orderPrimaryFilter(id), { $set: payload }, { upsert: true, new: true, setDefaultsOnInsert: true, lean: true }).exec();
    if (!persisted) return orderDocumentToDomain(payload);
    return orderDocumentToDomain(persisted);
  }
}

function userWhere(filter: Filters.UserQueryFilter | undefined): FilterQuery<UserDocument> {
  if (!filter) return {};
  const and: Record<string, unknown>[] = [];
  const emailFilter = filter.email;
  if (emailFilter?.eq !== undefined) and.push({ email: emailFilter.eq });
  if (emailFilter?.in?.length) and.push({ email: { $in: emailFilter.in } });
  if (typeof emailFilter?.contains === 'string' && emailFilter.contains.length > 0) and.push({ email: { $regex: escapeRegex(emailFilter.contains), $options: 'i' } });
  const userIdFilter = filter.userId;
  if (userIdFilter?.eq !== undefined) and.push({ userId: userIdFilter.eq });
  if (userIdFilter?.in?.length) and.push({ userId: { $in: userIdFilter.in } });
  if (typeof userIdFilter?.contains === 'string' && userIdFilter.contains.length > 0) and.push({ userId: { $regex: escapeRegex(userIdFilter.contains), $options: 'i' } });
  if (and.length === 0) return {};
  return { $and: and };
}

function userIdFromDomain(item: Domain.User): Persistence.UserId {
  return {
    userId: item.userId,
  };
}

function userPrimaryFilter(id: Persistence.UserId): Record<string, unknown> {
  return {
    userId: id.userId,
  };
}

function userSort(): Record<string, 1> {
  return {
    userId: 1,
  };
}

function userDocumentToDomain(doc: any): Domain.User {
  return {
    userId: doc.userId,
    email: doc.email,
  };
}

function userDomainToDocument(item: Domain.User): Record<string, unknown> {
  return {
    userId: item.userId,
    email: item.email,
  };
}

class UserMongooseRepository implements Persistence.UserRepository {
  constructor(private readonly model: Model<UserDocument>) {}

  async list(page: number, size: number): Promise<Persistence.Page<Domain.User>> {
    const normalized = normalizePage(page, size);
    const [rows, totalElements] = await Promise.all([
      this.model.find({}).sort(userSort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),
      this.model.countDocuments({}).exec(),
    ]);
    return {
      items: rows.map(userDocumentToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async getById(id: Persistence.UserId): Promise<Domain.User | null> {
    const row = await this.model.findOne(userPrimaryFilter(id)).lean().exec();
    return row ? userDocumentToDomain(row) : null;
  }

  async query(filter: Filters.UserQueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.User>> {
    const normalized = normalizePage(page, size);
    const where = userWhere(filter);
    const [rows, totalElements] = await Promise.all([
      this.model.find(where).sort(userSort()).skip(normalized.page * normalized.size).limit(normalized.size).lean().exec(),
      this.model.countDocuments(where).exec(),
    ]);
    return {
      items: rows.map(userDocumentToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async save(item: Domain.User): Promise<Domain.User> {
    const id = userIdFromDomain(item);
    const payload = userDomainToDocument(item);
    const persisted = await this.model.findOneAndUpdate(userPrimaryFilter(id), { $set: payload }, { upsert: true, new: true, setDefaultsOnInsert: true, lean: true }).exec();
    if (!persisted) return userDocumentToDomain(payload);
    return userDocumentToDomain(persisted);
  }
}
