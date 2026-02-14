package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;

/**
 * Signal event emitted for 'PaymentCaptured'.
 */
@Generated("prophet-cli")
public record PaymentCaptured(
    /**
     * Reference to the Order instance associated with this event.
     */
    OrderRef objectRef
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef objectRef;

        public Builder objectRef(OrderRef value) {
            this.objectRef = value;
            return this;
        }
        public PaymentCaptured build() {
            return new PaymentCaptured(
                objectRef
            );
        }
    }
}
