package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;

/**
 * Action output event emitted for 'OrderShippedEvent'.
 */
@Generated("prophet-cli")
public record OrderShippedEvent(
    /**
     * Reference to the Order instance associated with this event.
     */
    OrderRef objectRef,
    /**
     * Action output payload emitted by action 'shipOrder'.
     */
    @NotNull ShipOrderResult payload
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef objectRef;
        private ShipOrderResult payload;

        public Builder objectRef(OrderRef value) {
            this.objectRef = value;
            return this;
        }

        public Builder payload(ShipOrderResult value) {
            this.payload = value;
            return this;
        }
        public OrderShippedEvent build() {
            return new OrderShippedEvent(
                objectRef,
                payload
            );
        }
    }
}
