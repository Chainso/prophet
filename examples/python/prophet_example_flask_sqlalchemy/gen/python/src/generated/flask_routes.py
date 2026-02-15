# GENERATED FILE: do not edit directly.
from __future__ import annotations

import dataclasses

from flask import Blueprint, jsonify, request

from .action_handlers import GeneratedActionContext
from .action_service import GeneratedActionExecutionService
from .actions import *
from .persistence import GeneratedRepositories

def build_generated_blueprint(service: GeneratedActionExecutionService, context: GeneratedActionContext, repositories: GeneratedRepositories) -> Blueprint:
    bp = Blueprint('prophet_generated', __name__)

    @bp.post('/actions/approveOrder')
    def action_approveOrder():
        payload = request.get_json(silent=True) or {}
        input_model = ApproveOrderCommand(**payload)
        result = service.execute_approveOrder(input_model, context)
        return jsonify(dataclasses.asdict(result))

    @bp.post('/actions/createOrder')
    def action_createOrder():
        payload = request.get_json(silent=True) or {}
        input_model = CreateOrderCommand(**payload)
        result = service.execute_createOrder(input_model, context)
        return jsonify(dataclasses.asdict(result))

    @bp.post('/actions/shipOrder')
    def action_shipOrder():
        payload = request.get_json(silent=True) or {}
        input_model = ShipOrderCommand(**payload)
        result = service.execute_shipOrder(input_model, context)
        return jsonify(dataclasses.asdict(result))

    @bp.get('/orders')
    def list_order():
        page = int(request.args.get('page', 0))
        size = int(request.args.get('size', 20))
        result = repositories.order.list(page, size)
        return jsonify(dataclasses.asdict(result))

    @bp.get('/orders/<id>')
    def get_order(id):
        item = repositories.order.get_by_id(OrderRef(orderId=id))
        if item is None:
            return jsonify({'error': 'not_found'}), 404
        return jsonify(dataclasses.asdict(item))

    @bp.post('/orders/query')
    def query_order():
        page = int(request.args.get('page', 0))
        size = int(request.args.get('size', 20))
        payload = request.get_json(silent=True) or {}
        filter_model = OrderQueryFilter(**payload)
        result = repositories.order.query(filter_model, page, size)
        return jsonify(dataclasses.asdict(result))

    @bp.get('/users')
    def list_user():
        page = int(request.args.get('page', 0))
        size = int(request.args.get('size', 20))
        result = repositories.user.list(page, size)
        return jsonify(dataclasses.asdict(result))

    @bp.get('/users/<id>')
    def get_user(id):
        item = repositories.user.get_by_id(UserRef(userId=id))
        if item is None:
            return jsonify({'error': 'not_found'}), 404
        return jsonify(dataclasses.asdict(item))

    @bp.post('/users/query')
    def query_user():
        page = int(request.args.get('page', 0))
        size = int(request.args.get('size', 20))
        payload = request.get_json(silent=True) or {}
        filter_model = UserQueryFilter(**payload)
        result = repositories.user.query(filter_model, page, size)
        return jsonify(dataclasses.asdict(result))

    return bp
