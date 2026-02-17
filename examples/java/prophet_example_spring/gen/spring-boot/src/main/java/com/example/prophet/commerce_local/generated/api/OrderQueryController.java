package com.example.prophet.commerce_local.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.api.filters.OrderApprovalReasonFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderApprovedByUserIdFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderCustomerFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderDiscountCodeFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderOrderIdFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderQueryFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderShippingCarrierFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderShippingTrackingNumberFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderStateFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderTotalAmountFilter;
import com.example.prophet.commerce_local.generated.domain.Order;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import com.example.prophet.commerce_local.generated.mapping.OrderDomainMapper;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
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
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
@Generated("prophet-cli")
public class OrderQueryController {

    private final OrderRepository repository;
    private final OrderDomainMapper mapper;

    public OrderQueryController(OrderRepository repository, OrderDomainMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @GetMapping
    public ResponseEntity<OrderListResponse> list(
        @PageableDefault(size = 20) Pageable pageable
    ) {
        Specification<OrderEntity> spec = (root, query, cb) -> cb.conjunction();
        Page<OrderEntity> entityPage = repository.findAll(spec, pageable);
        List<Order> items = entityPage.stream().map(mapper::toDomain).toList();
        OrderListResponse result = OrderListResponse.builder()
            .items(items)
            .page(entityPage.getNumber())
            .size(entityPage.getSize())
            .totalElements(entityPage.getTotalElements())
            .totalPages(entityPage.getTotalPages())
            .build();
        return ResponseEntity.ok(result);
    }

    @PostMapping("/query")
    public ResponseEntity<OrderListResponse> query(
        @RequestBody(required = false) OrderQueryFilter filter,
        @PageableDefault(size = 20) Pageable pageable
    ) {
        Specification<OrderEntity> spec = (root, query, cb) -> cb.conjunction();
        if (filter != null) {
            if (filter.orderId() != null) {
                OrderOrderIdFilter orderIdFilter = filter.orderId();
                if (orderIdFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("orderId"), orderIdFilter.eq()));
                }
                if (orderIdFilter.in() != null && !orderIdFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("orderId").in(orderIdFilter.in()));
                }
                if (orderIdFilter.contains() != null && !orderIdFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("orderId")), "%" + orderIdFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.customer() != null) {
                OrderCustomerFilter customerFilter = filter.customer();
                if (customerFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.join("customer", JoinType.LEFT).get("userId"), customerFilter.eq()));
                }
                if (customerFilter.in() != null && !customerFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.join("customer", JoinType.LEFT).get("userId").in(customerFilter.in()));
                }
            }
            if (filter.totalAmount() != null) {
                OrderTotalAmountFilter totalAmountFilter = filter.totalAmount();
                if (totalAmountFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("totalAmount"), totalAmountFilter.eq()));
                }
                if (totalAmountFilter.in() != null && !totalAmountFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("totalAmount").in(totalAmountFilter.in()));
                }
                if (totalAmountFilter.gte() != null) {
                    spec = spec.and((root, query, cb) -> cb.greaterThanOrEqualTo(root.<BigDecimal>get("totalAmount"), totalAmountFilter.gte()));
                }
                if (totalAmountFilter.lte() != null) {
                    spec = spec.and((root, query, cb) -> cb.lessThanOrEqualTo(root.<BigDecimal>get("totalAmount"), totalAmountFilter.lte()));
                }
            }
            if (filter.discountCode() != null) {
                OrderDiscountCodeFilter discountCodeFilter = filter.discountCode();
                if (discountCodeFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("discountCode"), discountCodeFilter.eq()));
                }
                if (discountCodeFilter.in() != null && !discountCodeFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("discountCode").in(discountCodeFilter.in()));
                }
                if (discountCodeFilter.contains() != null && !discountCodeFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("discountCode")), "%" + discountCodeFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.approvedByUserId() != null) {
                OrderApprovedByUserIdFilter approvedByUserIdFilter = filter.approvedByUserId();
                if (approvedByUserIdFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("approvedByUserId"), approvedByUserIdFilter.eq()));
                }
                if (approvedByUserIdFilter.in() != null && !approvedByUserIdFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("approvedByUserId").in(approvedByUserIdFilter.in()));
                }
                if (approvedByUserIdFilter.contains() != null && !approvedByUserIdFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("approvedByUserId")), "%" + approvedByUserIdFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.approvalReason() != null) {
                OrderApprovalReasonFilter approvalReasonFilter = filter.approvalReason();
                if (approvalReasonFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("approvalReason"), approvalReasonFilter.eq()));
                }
                if (approvalReasonFilter.in() != null && !approvalReasonFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("approvalReason").in(approvalReasonFilter.in()));
                }
                if (approvalReasonFilter.contains() != null && !approvalReasonFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("approvalReason")), "%" + approvalReasonFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.shippingCarrier() != null) {
                OrderShippingCarrierFilter shippingCarrierFilter = filter.shippingCarrier();
                if (shippingCarrierFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("shippingCarrier"), shippingCarrierFilter.eq()));
                }
                if (shippingCarrierFilter.in() != null && !shippingCarrierFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("shippingCarrier").in(shippingCarrierFilter.in()));
                }
                if (shippingCarrierFilter.contains() != null && !shippingCarrierFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("shippingCarrier")), "%" + shippingCarrierFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.shippingTrackingNumber() != null) {
                OrderShippingTrackingNumberFilter shippingTrackingNumberFilter = filter.shippingTrackingNumber();
                if (shippingTrackingNumberFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("shippingTrackingNumber"), shippingTrackingNumberFilter.eq()));
                }
                if (shippingTrackingNumberFilter.in() != null && !shippingTrackingNumberFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("shippingTrackingNumber").in(shippingTrackingNumberFilter.in()));
                }
                if (shippingTrackingNumberFilter.contains() != null && !shippingTrackingNumberFilter.contains().isBlank()) {
                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get("shippingTrackingNumber")), "%" + shippingTrackingNumberFilter.contains().toLowerCase() + "%"));
                }
            }
            if (filter.state() != null) {
                OrderStateFilter stateFilter = filter.state();
                if (stateFilter.eq() != null) {
                    spec = spec.and((root, query, cb) -> cb.equal(root.get("state"), stateFilter.eq()));
                }
                if (stateFilter.in() != null && !stateFilter.in().isEmpty()) {
                    spec = spec.and((root, query, cb) -> root.get("state").in(stateFilter.in()));
                }
            }
        }
        Page<OrderEntity> entityPage = repository.findAll(spec, pageable);
        List<Order> items = entityPage.stream().map(mapper::toDomain).toList();
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

        Order domain = mapper.toDomain(maybeEntity.get());
        return ResponseEntity.ok(domain);
    }
}
