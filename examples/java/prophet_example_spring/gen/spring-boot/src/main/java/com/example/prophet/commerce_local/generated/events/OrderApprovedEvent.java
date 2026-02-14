package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;

/**
 * Action output event emitted for 'OrderApprovedEvent'.
 */
@Generated("prophet-cli")
public record OrderApprovedEvent(
    /**
     * Reference to the Order instance associated with this event.
     */
    OrderRef objectRef,
    /**
     * Action output payload emitted by action 'approveOrder'.
     */
    @NotNull ApproveOrderResult payload
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef objectRef;
        private ApproveOrderResult payload;

        public Builder objectRef(OrderRef value) {
            this.objectRef = value;
            return this;
        }

        public Builder payload(ApproveOrderResult value) {
            this.payload = value;
            return this;
        }
        public OrderApprovedEvent build() {
            return new OrderApprovedEvent(
                objectRef,
                payload
            );
        }
    }
}
