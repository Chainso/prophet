package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Order;
import com.example.prophet.generated.domain.OrderState;
import com.example.prophet.generated.domain.UserRef;
import com.example.prophet.generated.persistence.OrderEntity;
import com.example.prophet.generated.persistence.OrderRepository;
import java.util.Optional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
@Generated("prophet-cli")
public class OrderQueryController {

    private final OrderRepository repository;

    public OrderQueryController(OrderRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<Order> getById(@PathVariable("orderId") String orderId) {
        Optional<OrderEntity> maybeEntity = repository.findById(orderId);
        if (maybeEntity.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        OrderEntity entity = maybeEntity.get();
        Order domain = new Order(
            new UserRef(entity.getCustomer().getUserId()),
            entity.getDiscountCode(),
            entity.getOrderId(),
            entity.getShippingAddress(),
            entity.getTags(),
            entity.getTotalAmount(),
            entity.getCurrentState()
        );
        return ResponseEntity.ok(domain);
    }
}
