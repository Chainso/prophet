package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.NOT_FOUND;

@Component
public class ShipOrderHandler implements ShipOrderActionHandler {

    private final OrderRepository orderRepository;

    public ShipOrderHandler(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    @Transactional
    public ShipOrderResult handle(ShipOrderCommand request) {
        String orderId = request.order().orderId();
        OrderEntity order = orderRepository.findById(orderId)
            .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Order not found: " + orderId));

        if (order.getCurrentState() != OrderState.APPROVED) {
            throw new ResponseStatusException(
                BAD_REQUEST,
                "Order must be in APPROVED state before shipping. Current state: " + order.getCurrentState()
            );
        }

        order.setCurrentState(OrderState.SHIPPED);
        orderRepository.save(order);

        List<String> labels = request.packageIds()
            .stream()
            .map(id -> request.carrier() + "-" + request.trackingNumber() + "-" + id)
            .toList();

        return new ShipOrderResult(
            OrderRef.builder().orderId(order.getOrderId()).build(),
            "shipped",
            labels,
            List.of(labels)
        );
    }
}
