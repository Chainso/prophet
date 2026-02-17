package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.CreateOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import com.example.prophet.commerce_local.generated.events.CreateOrderResult;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import com.example.prophet.commerce_local.generated.persistence.UserEntity;
import com.example.prophet.commerce_local.generated.persistence.UserRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Component
public class CreateOrderHandler implements CreateOrderActionHandler {

    private final OrderRepository orderRepository;
    private final UserRepository userRepository;

    public CreateOrderHandler(OrderRepository orderRepository, UserRepository userRepository) {
        this.orderRepository = orderRepository;
        this.userRepository = userRepository;
    }

    @Override
    @Transactional
    public CreateOrderResult handle(CreateOrderCommand request) {
        String mintedOrderId = UUID.randomUUID().toString();
        while (orderRepository.existsById(mintedOrderId)) {
            mintedOrderId = UUID.randomUUID().toString();
        }

        UserEntity customer = userRepository.findById(request.customer().userId())
            .orElseGet(() -> createDefaultUser(request.customer().userId()));

        OrderEntity order = new OrderEntity();
        order.setOrderId(mintedOrderId);
        order.setCustomer(customer);
        order.setTotalAmount(request.totalAmount());
        order.setDiscountCode(request.discountCode());
        order.setTags(request.tags());
        order.setShippingAddress(request.shippingAddress());
        order.setState(OrderState.CREATED);
        orderRepository.save(order);

        return new CreateOrderResult(OrderRef.builder().orderId(order.getOrderId()).build());
    }

    private UserEntity createDefaultUser(String userId) {
        UserEntity user = new UserEntity();
        user.setUserId(userId);
        user.setEmail(userId + "@example.local");
        return userRepository.save(user);
    }
}
