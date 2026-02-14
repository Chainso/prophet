package com.example.prophet.commerce_local.generated.mapping;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Order;
import com.example.prophet.commerce_local.generated.domain.UserRef;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class OrderDomainMapper {
    public Order toDomain(OrderEntity entity) {
        if (entity == null) {
            return null;
        }
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
