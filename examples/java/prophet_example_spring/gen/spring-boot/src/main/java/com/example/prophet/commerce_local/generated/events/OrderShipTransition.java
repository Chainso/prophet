package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;

/**
 * Emit 'OrderShipTransition'.
 */
@Generated("prophet-cli")
public record OrderShipTransition(
    /**
     * Reference to the Order instance associated with this transition.
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
        public OrderShipTransition build() {
            return new OrderShipTransition(
                objectRef
            );
        }
    }
}
