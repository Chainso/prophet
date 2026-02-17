package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import jakarta.validation.constraints.NotNull;

/**
 * Event payload for 'CreateOrderResult'.
 */
@Generated("prophet-cli")
public record CreateOrderResult(
    @NotNull OrderRefOrObject order
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRefOrObject order;

        public Builder order(OrderRefOrObject value) {
            this.order = value;
            return this;
        }
        public CreateOrderResult build() {
            return new CreateOrderResult(
                order
            );
        }
    }
}
