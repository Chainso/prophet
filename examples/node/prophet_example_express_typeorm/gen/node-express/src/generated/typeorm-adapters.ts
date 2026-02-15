// GENERATED FILE: do not edit directly.

import type * as Domain from './domain';
import type * as Filters from './query';
import type * as Persistence from './persistence';

export class TypeOrmGeneratedRepositories implements Persistence.GeneratedRepositories {
  order: Persistence.OrderRepository = new OrderTypeOrmRepository();
  user: Persistence.UserRepository = new UserTypeOrmRepository();
}

class OrderTypeOrmRepository implements Persistence.OrderRepository {
  async list(_page: number, _size: number): Promise<Persistence.Page<Domain.Order>> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async getById(_id: Persistence.OrderId): Promise<Domain.Order | null> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async query(_filter: Filters.OrderQueryFilter, _page: number, _size: number): Promise<Persistence.Page<Domain.Order>> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async save(_item: Domain.Order): Promise<Domain.Order> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
}

class UserTypeOrmRepository implements Persistence.UserRepository {
  async list(_page: number, _size: number): Promise<Persistence.Page<Domain.User>> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async getById(_id: Persistence.UserId): Promise<Domain.User | null> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async query(_filter: Filters.UserQueryFilter, _page: number, _size: number): Promise<Persistence.Page<Domain.User>> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
  async save(_item: Domain.User): Promise<Domain.User> {
    throw new Error('TypeORM adapter scaffolding generated; implement repository binding logic.');
  }
}
