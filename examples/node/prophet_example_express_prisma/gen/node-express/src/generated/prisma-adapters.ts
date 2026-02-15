// GENERATED FILE: do not edit directly.

import type { PrismaClient } from '@prisma/client';
import type * as Domain from './domain';
import type * as Filters from './query';
import type * as Persistence from './persistence';

function normalizePage(page: number, size: number): { page: number; size: number } {
  const normalizedPage = Number.isFinite(page) && page >= 0 ? Math.trunc(page) : 0;
  const normalizedSize = Number.isFinite(size) && size > 0 ? Math.trunc(size) : 20;
  return { page: normalizedPage, size: normalizedSize };
}

function totalPages(totalElements: number, size: number): number {
  if (size <= 0) return 0;
  return Math.ceil(totalElements / size);
}

export class PrismaGeneratedRepositories implements Persistence.GeneratedRepositories {
  order: Persistence.OrderRepository;
  user: Persistence.UserRepository;

  constructor(private readonly client: PrismaClient) {
    this.order = new OrderPrismaRepository(client);
    this.user = new UserPrismaRepository(client);
  }
}

function orderWhere(filter: Filters.OrderQueryFilter | undefined): any {
  if (!filter) return {};
  const and: any[] = [];
  const customerFilter = filter.customer;
  if (customerFilter?.eq !== undefined) {
    and.push({ customer_user_id: customerFilter.eq.userId });
  }
  if (customerFilter?.in?.length) {
    and.push({
      OR: customerFilter.in.map((entry) => ({
        customer_user_id: entry.userId,
      })),
    });
  }
  const discountCodeFilter = filter.discountCode;
  if (discountCodeFilter?.eq !== undefined) and.push({ discount_code: discountCodeFilter.eq });
  if (discountCodeFilter?.in?.length) and.push({ discount_code: { in: discountCodeFilter.in } });
  if (typeof discountCodeFilter?.contains === 'string' && discountCodeFilter.contains.length > 0) and.push({ discount_code: { contains: discountCodeFilter.contains } });
  const orderIdFilter = filter.orderId;
  if (orderIdFilter?.eq !== undefined) and.push({ order_id: orderIdFilter.eq });
  if (orderIdFilter?.in?.length) and.push({ order_id: { in: orderIdFilter.in } });
  if (typeof orderIdFilter?.contains === 'string' && orderIdFilter.contains.length > 0) and.push({ order_id: { contains: orderIdFilter.contains } });
  const totalAmountFilter = filter.totalAmount;
  if (totalAmountFilter?.eq !== undefined) and.push({ total_amount: totalAmountFilter.eq });
  if (totalAmountFilter?.in?.length) and.push({ total_amount: { in: totalAmountFilter.in } });
  if (totalAmountFilter?.gte !== undefined) and.push({ total_amount: { gte: totalAmountFilter.gte } });
  if (totalAmountFilter?.lte !== undefined) and.push({ total_amount: { lte: totalAmountFilter.lte } });
  const currentStateFilter = filter.currentState;
  if (currentStateFilter?.eq !== undefined) and.push({ current_state: currentStateFilter.eq });
  if (currentStateFilter?.in?.length) and.push({ current_state: { in: currentStateFilter.in } });
  if (and.length === 0) return {};
  return { AND: and };
}

function orderIdFromDomain(item: Domain.Order): Persistence.OrderId {
  return {
    orderId: item.orderId,
  };
}

function orderUniqueWhere(id: Persistence.OrderId): any {
  return { order_id: id.orderId };
}

function orderRowToDomain(row: any): Domain.Order {
  return {
    orderId: row.order_id,
    customer: {
      userId: row.customer_user_id,
    },
    totalAmount: row.total_amount,
    discountCode: row.discount_code ?? undefined,
    tags: row.tags ?? undefined,
    shippingAddress: row.shipping_address ?? undefined,
    currentState: row.current_state,
  };
}

function orderDomainToRow(item: Domain.Order): any {
  return {
    order_id: item.orderId,
    customer_user_id: item.customer.userId,
    total_amount: item.totalAmount,
    discount_code: item.discountCode ?? null,
    tags: item.tags ?? null,
    shipping_address: item.shippingAddress ?? null,
    current_state: item.currentState,
  };
}

class OrderPrismaRepository implements Persistence.OrderRepository {
  private readonly delegate: any;

  constructor(client: PrismaClient) {
    this.delegate = (client as any).order;
  }

  async list(page: number, size: number): Promise<Persistence.Page<Domain.Order>> {
    const normalized = normalizePage(page, size);
    const [rows, totalElements] = await Promise.all([
      this.delegate.findMany({
        skip: normalized.page * normalized.size,
        take: normalized.size,
        orderBy: [
          { order_id: 'asc' },
        ],
      }),
      this.delegate.count(),
    ]);
    return {
      items: rows.map(orderRowToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async getById(id: Persistence.OrderId): Promise<Domain.Order | null> {
    const row = await this.delegate.findUnique({ where: orderUniqueWhere(id) });
    return row ? orderRowToDomain(row) : null;
  }

  async query(filter: Filters.OrderQueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.Order>> {
    const normalized = normalizePage(page, size);
    const where = orderWhere(filter);
    const [rows, totalElements] = await Promise.all([
      this.delegate.findMany({
        where,
        skip: normalized.page * normalized.size,
        take: normalized.size,
        orderBy: [
          { order_id: 'asc' },
        ],
      }),
      this.delegate.count({ where }),
    ]);
    return {
      items: rows.map(orderRowToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async save(item: Domain.Order): Promise<Domain.Order> {
    const payload = orderDomainToRow(item);
    const persisted = await this.delegate.upsert({ where: orderUniqueWhere(orderIdFromDomain(item)), create: payload, update: payload });
    return orderRowToDomain(persisted);
  }
}

function userWhere(filter: Filters.UserQueryFilter | undefined): any {
  if (!filter) return {};
  const and: any[] = [];
  const emailFilter = filter.email;
  if (emailFilter?.eq !== undefined) and.push({ email: emailFilter.eq });
  if (emailFilter?.in?.length) and.push({ email: { in: emailFilter.in } });
  if (typeof emailFilter?.contains === 'string' && emailFilter.contains.length > 0) and.push({ email: { contains: emailFilter.contains } });
  const userIdFilter = filter.userId;
  if (userIdFilter?.eq !== undefined) and.push({ user_id: userIdFilter.eq });
  if (userIdFilter?.in?.length) and.push({ user_id: { in: userIdFilter.in } });
  if (typeof userIdFilter?.contains === 'string' && userIdFilter.contains.length > 0) and.push({ user_id: { contains: userIdFilter.contains } });
  if (and.length === 0) return {};
  return { AND: and };
}

function userIdFromDomain(item: Domain.User): Persistence.UserId {
  return {
    userId: item.userId,
  };
}

function userUniqueWhere(id: Persistence.UserId): any {
  return { user_id: id.userId };
}

function userRowToDomain(row: any): Domain.User {
  return {
    userId: row.user_id,
    email: row.email,
  };
}

function userDomainToRow(item: Domain.User): any {
  return {
    user_id: item.userId,
    email: item.email,
  };
}

class UserPrismaRepository implements Persistence.UserRepository {
  private readonly delegate: any;

  constructor(client: PrismaClient) {
    this.delegate = (client as any).user;
  }

  async list(page: number, size: number): Promise<Persistence.Page<Domain.User>> {
    const normalized = normalizePage(page, size);
    const [rows, totalElements] = await Promise.all([
      this.delegate.findMany({
        skip: normalized.page * normalized.size,
        take: normalized.size,
        orderBy: [
          { user_id: 'asc' },
        ],
      }),
      this.delegate.count(),
    ]);
    return {
      items: rows.map(userRowToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async getById(id: Persistence.UserId): Promise<Domain.User | null> {
    const row = await this.delegate.findUnique({ where: userUniqueWhere(id) });
    return row ? userRowToDomain(row) : null;
  }

  async query(filter: Filters.UserQueryFilter, page: number, size: number): Promise<Persistence.Page<Domain.User>> {
    const normalized = normalizePage(page, size);
    const where = userWhere(filter);
    const [rows, totalElements] = await Promise.all([
      this.delegate.findMany({
        where,
        skip: normalized.page * normalized.size,
        take: normalized.size,
        orderBy: [
          { user_id: 'asc' },
        ],
      }),
      this.delegate.count({ where }),
    ]);
    return {
      items: rows.map(userRowToDomain),
      page: normalized.page,
      size: normalized.size,
      totalElements,
      totalPages: totalPages(totalElements, normalized.size),
    };
  }

  async save(item: Domain.User): Promise<Domain.User> {
    const payload = userDomainToRow(item);
    const persisted = await this.delegate.upsert({ where: userUniqueWhere(userIdFromDomain(item)), create: payload, update: payload });
    return userRowToDomain(persisted);
  }
}
