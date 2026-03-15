package com.example.prophet.commerce_local.generated.api.filters;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderStatus;
import java.util.List;

@Generated("prophet-cli")
public record OrderStatusFilter(
    OrderStatus eq,
    List<OrderStatus> in
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderStatus eq;
        private List<OrderStatus> in;

        public Builder eq(OrderStatus value) {
            this.eq = value;
            return this;
        }

        public Builder in(List<OrderStatus> value) {
            this.in = value;
            return this;
        }
        public OrderStatusFilter build() {
            return new OrderStatusFilter(
                eq,
                in
            );
        }
    }
}
