package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
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
public class ApproveOrderHandler implements ApproveOrderActionHandler {

    private final OrderRepository orderRepository;

    public ApproveOrderHandler(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    @Transactional
    public ApproveOrderResult handle(ApproveOrderCommand request) {
        OrderEntity order = orderRepository.findById(request.orderId())
            .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Order not found: " + request.orderId()));

        if (order.getCurrentState() != OrderState.CREATED) {
            throw new ResponseStatusException(
                BAD_REQUEST,
                "Order must be in CREATED state before approval. Current state: " + order.getCurrentState()
            );
        }

        order.setCurrentState(OrderState.APPROVED);
        orderRepository.save(order);

        return new ApproveOrderResult(order.getOrderId(), "approved", List.of());
    }
}
