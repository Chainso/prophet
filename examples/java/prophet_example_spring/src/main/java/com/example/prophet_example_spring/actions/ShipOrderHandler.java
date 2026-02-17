package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ShipOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ShipOrderActionHandler;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.mapping.OrderDomainMapper;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import com.example.prophet.commerce_local.generated.transitions.services.OrderTransitionService;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class ShipOrderHandler implements ShipOrderActionHandler {

    private final OrderRepository orderRepository;
    private final OrderDomainMapper orderDomainMapper;
    private final OrderTransitionService orderTransitionService;

    public ShipOrderHandler(
        OrderRepository orderRepository,
        OrderDomainMapper orderDomainMapper,
        OrderTransitionService orderTransitionService
    ) {
        this.orderRepository = orderRepository;
        this.orderDomainMapper = orderDomainMapper;
        this.orderTransitionService = orderTransitionService;
    }

    @Override
    @Transactional
    public OrderShipTransition handle(ShipOrderCommand request) {
        OrderEntity order = orderRepository.findById(request.order().orderId())
            .orElseThrow(() -> new IllegalArgumentException("order not found: " + request.order().orderId()));

        order.setShippingCarrier(request.carrier());
        order.setShippingTrackingNumber(request.trackingNumber());
        order.setShippingPackageIds(request.packageIds());
        order = orderRepository.save(order);

        return orderTransitionService
            .shipOrder(orderDomainMapper.toDomain(order))
            .builder()
            .carrier(request.carrier())
            .trackingNumber(request.trackingNumber())
            .packageIds(request.packageIds())
            .build();
    }
}
