package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.transitions.services.OrderTransitionService;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class ShipOrderHandler implements ShipOrderActionHandler {

    private final OrderTransitionService orderTransitionService;

    public ShipOrderHandler(OrderTransitionService orderTransitionService) {
        this.orderTransitionService = orderTransitionService;
    }

    @Override
    @Transactional
    public OrderShipTransition handle(ShipOrderCommand request) {
        return orderTransitionService
            .shipOrder(OrderRef.builder().orderId(request.order().orderId()).build())
            .build();
    }
}
