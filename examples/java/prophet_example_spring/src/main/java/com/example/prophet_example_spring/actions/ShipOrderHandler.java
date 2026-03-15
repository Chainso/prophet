package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderStatus;
import com.example.prophet.commerce_local.generated.events.OrderShipped;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class ShipOrderHandler implements ShipOrderActionHandler {

    private final OrderRepository orderRepository;

    public ShipOrderHandler(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    @Transactional
    public OrderShipped handle(ShipOrderCommand request) {
        OrderEntity order = orderRepository.findById(request.order().orderId())
            .orElseThrow(() -> new IllegalArgumentException("order not found: " + request.order().orderId()));

        order.setShippingCarrier(request.carrier());
        order.setShippingTrackingNumber(request.trackingNumber());
        order.setShippingPackageIds(request.packageIds());
        order.setStatus(OrderStatus.Shipped);
        order = orderRepository.save(order);

        return OrderShipped.builder()
            .order(OrderRef.builder().orderId(order.getOrderId()).build())
            .build();
    }
}
