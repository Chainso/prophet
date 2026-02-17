package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;

/**
 * Event payload for 'OrderShipTransition'.
 */
@Generated("prophet-cli")
public record OrderShipTransition(
    /**
     * Reference or full Order instance associated with this transition.
     */
    OrderRefOrObject objectRef
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRefOrObject objectRef;

        public Builder objectRef(OrderRefOrObject value) {
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
