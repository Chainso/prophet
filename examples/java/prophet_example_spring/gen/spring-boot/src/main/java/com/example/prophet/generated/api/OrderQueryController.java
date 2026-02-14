package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Order;
import com.example.prophet.generated.domain.OrderState;
import com.example.prophet.generated.domain.UserRef;
import com.example.prophet.generated.persistence.OrderEntity;
import com.example.prophet.generated.persistence.OrderRepository;
import jakarta.persistence.criteria.JoinType;
import java.math.BigDecimal;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
@Generated("prophet-cli")
public class OrderQueryController {

    private final OrderRepository repository;

    public OrderQueryController(OrderRepository repository) {
        this.repository = repository;
    }

    @GetMapping
    public ResponseEntity<Page<Order>> list(
        @RequestParam(name = "orderId", required = false) String orderId,
        @RequestParam(name = "customerUserId", required = false) String customerUserId,
        @RequestParam(name = "totalAmount", required = false) BigDecimal totalAmount,
        @RequestParam(name = "discountCode", required = false) String discountCode,
        @RequestParam(name = "currentState", required = false) OrderState currentState,
        @PageableDefault(size = 20) Pageable pageable
    ) {
        Specification<OrderEntity> spec = (root, query, cb) -> cb.conjunction();
        if (orderId != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("orderId"), orderId));
        }
        if (customerUserId != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.join("customer", JoinType.LEFT).get("userId"), customerUserId));
        }
        if (totalAmount != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("totalAmount"), totalAmount));
        }
        if (discountCode != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("discountCode"), discountCode));
        }
        if (currentState != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("currentState"), currentState));
        }
        Page<Order> result = repository.findAll(spec, pageable).map(this::toDomain);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<Order> getById(@PathVariable("orderId") String orderId) {
        Optional<OrderEntity> maybeEntity = repository.findById(orderId);
        if (maybeEntity.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Order domain = toDomain(maybeEntity.get());
        return ResponseEntity.ok(domain);
    }
    private Order toDomain(OrderEntity entity) {
        return new Order(
            entity.getOrderId(),
            entity.getCustomer() == null ? null : new UserRef(entity.getCustomer().getUserId()),
            entity.getTotalAmount(),
            entity.getDiscountCode(),
            entity.getTags(),
            entity.getShippingAddress(),
            entity.getCurrentState()
        );
    }

}
