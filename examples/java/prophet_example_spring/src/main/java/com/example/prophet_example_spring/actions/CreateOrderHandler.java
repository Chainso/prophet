package com.example.prophet_example_spring.actions;

import com.example.prophet.generated.actions.CreateOrderCommand;
import com.example.prophet.generated.actions.CreateOrderResult;
import com.example.prophet.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.generated.domain.OrderState;
import com.example.prophet.generated.persistence.OrderEntity;
import com.example.prophet.generated.persistence.OrderRepository;
import com.example.prophet.generated.persistence.UserEntity;
import com.example.prophet.generated.persistence.UserRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

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
        if (orderRepository.existsById(request.orderId())) {
            throw new ResponseStatusException(BAD_REQUEST, "Order already exists: " + request.orderId());
        }

        UserEntity customer = userRepository.findById(request.customer().userId())
            .orElseGet(() -> createDefaultUser(request.customer().userId()));

        OrderEntity order = new OrderEntity();
        order.setOrderId(request.orderId());
        order.setCustomer(customer);
        order.setTotalAmount(request.totalAmount());
        order.setDiscountCode(request.discountCode());
        order.setTags(request.tags());
        order.setShippingAddress(request.shippingAddress());
        order.setCurrentState(OrderState.CREATED);
        orderRepository.save(order);

        return new CreateOrderResult(order.getOrderId(), order.getCurrentState().name().toLowerCase());
    }

    private UserEntity createDefaultUser(String userId) {
        UserEntity user = new UserEntity();
        user.setUserId(userId);
        user.setEmail(userId + "@example.local");
        return userRepository.save(user);
    }
}
