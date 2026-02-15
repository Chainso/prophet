package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;

/**
 * Emit 'PaymentCaptured'.
 */
@Generated("prophet-cli")
public record PaymentCaptured(
    @NotNull OrderRef order
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef order;

        public Builder order(OrderRef value) {
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
