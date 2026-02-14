package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Order;
import com.example.prophet.generated.domain.OrderState;
import com.example.prophet.generated.domain.UserRef;
import com.example.prophet.generated.persistence.OrderEntity;
import com.example.prophet.generated.persistence.OrderRepository;
import jakarta.persistence.criteria.JoinType;
import java.math.BigDecimal;
import java.util.List;
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
    public ResponseEntity<OrderListResponse> list(
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
        Page<OrderEntity> entityPage = repository.findAll(spec, pageable);
        List<Order> items = entityPage.stream().map(this::toDomain).toList();
        OrderListResponse result = OrderListResponse.builder()
            .items(items)
            .page(entityPage.getNumber())
            .size(entityPage.getSize())
            .totalElements(entityPage.getTotalElements())
            .totalPages(entityPage.getTotalPages())
            .build();
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
        return Order.builder()
            .orderId(entity.getOrderId())
            .customer(entity.getCustomer() == null ? null : UserRef.builder().userId(entity.getCustomer().getUserId()).build())
            .totalAmount(entity.getTotalAmount())
            .discountCode(entity.getDiscountCode())
            .tags(entity.getTags())
            .shippingAddress(entity.getShippingAddress())
            .currentState(entity.getCurrentState())
            .build();
    }

}
