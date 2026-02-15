package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;

/**
 * Event payload for 'OrderApproveTransition'.
 */
@Generated("prophet-cli")
public record OrderApproveTransition(
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
        public OrderApproveTransition build() {
            return new OrderApproveTransition(
                objectRef
            );
        }
    }
}
