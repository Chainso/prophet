// GENERATED FILE: do not edit directly.

import { Router, type Request, type Response, type NextFunction } from 'express';
import { GeneratedActionExecutionService } from './action-service.js';
import type { GeneratedActionContext } from './action-handlers.js';
import * as Schemas from './validation.js';

export function buildGeneratedActionRouter(
  service: GeneratedActionExecutionService,
  context: GeneratedActionContext,
): Router {
  const router = Router();

  router.post('/actions/approveOrder', async (req: Request, res: Response, next: NextFunction) => {
    const parsed = Schemas.ApproveOrderCommandSchema.safeParse(req.body ?? {});
    if (!parsed.success) {
      res.status(400).json({ error: 'invalid_request', details: parsed.error.format() });
      return;
    }
    try {
      const output = await service.approveOrder(parsed.data, context);
      res.json(output);
    } catch (error) {
      next(error);
    }
  });

  router.post('/actions/createOrder', async (req: Request, res: Response, next: NextFunction) => {
    const parsed = Schemas.CreateOrderCommandSchema.safeParse(req.body ?? {});
    if (!parsed.success) {
      res.status(400).json({ error: 'invalid_request', details: parsed.error.format() });
      return;
    }
    try {
      const output = await service.createOrder(parsed.data, context);
      res.json(output);
    } catch (error) {
      next(error);
    }
  });

  router.post('/actions/shipOrder', async (req: Request, res: Response, next: NextFunction) => {
    const parsed = Schemas.ShipOrderCommandSchema.safeParse(req.body ?? {});
    if (!parsed.success) {
      res.status(400).json({ error: 'invalid_request', details: parsed.error.format() });
      return;
    }
    try {
      const output = await service.shipOrder(parsed.data, context);
      res.json(output);
    } catch (error) {
      next(error);
    }
  });

  return router;
}
