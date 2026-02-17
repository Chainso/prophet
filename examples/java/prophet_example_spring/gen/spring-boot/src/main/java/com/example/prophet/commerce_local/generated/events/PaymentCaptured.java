package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import jakarta.validation.constraints.NotNull;

/**
 * Event payload for 'PaymentCaptured'.
 */
@Generated("prophet-cli")
public record PaymentCaptured(
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
        public PaymentCaptured build() {
            return new PaymentCaptured(
                order
            );
        }
    }
}
