package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;

/**
 * Action output event emitted for 'OrderCreatedEvent'.
 */
@Generated("prophet-cli")
public record OrderCreatedEvent(
    /**
     * Reference to the Order instance associated with this event.
     */
    OrderRef objectRef,
    /**
     * Action output payload emitted by action 'createOrder'.
     */
    @NotNull CreateOrderResult payload
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef objectRef;
        private CreateOrderResult payload;

        public Builder objectRef(OrderRef value) {
            this.objectRef = value;
            return this;
        }

        public Builder payload(CreateOrderResult value) {
            this.payload = value;
            return this;
        }
        public OrderCreatedEvent build() {
            return new OrderCreatedEvent(
                objectRef,
                payload
            );
        }
    }
}
