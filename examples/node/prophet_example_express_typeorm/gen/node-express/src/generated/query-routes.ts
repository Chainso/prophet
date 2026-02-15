// GENERATED FILE: do not edit directly.

import { Router, type Request, type Response, type NextFunction } from 'express';
import type { GeneratedRepositories } from './persistence';
import type * as Filters from './query';

function parsePage(value: unknown, fallback: number): number {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) return fallback;
  return Math.trunc(n);
}

export function buildGeneratedQueryRouter(repositories: GeneratedRepositories): Router {
  const router = Router();

  router.get('/orders', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const page = parsePage(req.query.page, 0);
      const size = parsePage(req.query.size, 20);
      const result = await repositories.order.list(page, size);
      res.json(result);
    } catch (error) {
      next(error);
    }
  });

  router.get('/orders/:id', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = {
        orderId: String(req.params['id']),
      };
      const item = await repositories.order.getById(id);
      if (!item) {
        res.status(404).json({ error: 'not_found' });
        return;
      }
      res.json(item);
    } catch (error) {
      next(error);
    }
  });

  router.post('/orders/query', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const page = parsePage(req.query.page, 0);
      const size = parsePage(req.query.size, 20);
      const filter = (req.body ?? {}) as Filters.OrderQueryFilter;
      const result = await repositories.order.query(filter, page, size);
      res.json(result);
    } catch (error) {
      next(error);
    }
  });

  router.get('/users', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const page = parsePage(req.query.page, 0);
      const size = parsePage(req.query.size, 20);
      const result = await repositories.user.list(page, size);
      res.json(result);
    } catch (error) {
      next(error);
    }
  });

  router.get('/users/:id', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = {
        userId: String(req.params['id']),
      };
      const item = await repositories.user.getById(id);
      if (!item) {
        res.status(404).json({ error: 'not_found' });
        return;
      }
      res.json(item);
    } catch (error) {
      next(error);
    }
  });

  router.post('/users/query', async (req: Request, res: Response, next: NextFunction) => {
    try {
      const page = parsePage(req.query.page, 0);
      const size = parsePage(req.query.size, 20);
      const filter = (req.body ?? {}) as Filters.UserQueryFilter;
      const result = await repositories.user.query(filter, page, size);
      res.json(result);
    } catch (error) {
      next(error);
    }
  });

  return router;
}
