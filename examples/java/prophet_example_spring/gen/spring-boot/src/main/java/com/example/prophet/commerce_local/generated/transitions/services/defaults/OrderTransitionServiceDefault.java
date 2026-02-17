package com.example.prophet.commerce_local.generated.transitions.services.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransitionDraft;
import com.example.prophet.commerce_local.generated.events.OrderShipTransitionDraft;
import com.example.prophet.commerce_local.generated.transitions.handlers.OrderTransitionHandler;
import com.example.prophet.commerce_local.generated.transitions.services.OrderTransitionService;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class OrderTransitionServiceDefault implements OrderTransitionService {
    private final ObjectProvider<OrderTransitionHandler> handlerProvider;

    public OrderTransitionServiceDefault(ObjectProvider<OrderTransitionHandler> handlerProvider) {
        this.handlerProvider = handlerProvider;
    }

    @Override
    public OrderApproveTransitionDraft approveOrder(OrderRefOrObject target) {
        OrderTransitionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No transition handler bean provided for object 'Order'");
        }
        return handler.approveOrder(target);
    }

    @Override
    public OrderShipTransitionDraft shipOrder(OrderRefOrObject target) {
        OrderTransitionHandler handler = handlerProvider.getIfAvailable();
        if (handler == null) {
            throw new UnsupportedOperationException("No transition handler bean provided for object 'Order'");
        }
        return handler.shipOrder(target);
    }
}
