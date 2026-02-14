package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import jakarta.validation.constraints.NotNull;

/**
 * Transition event emitted for 'OrderApprovedTransition'.
 */
@Generated("prophet-cli")
public record OrderApprovedTransition(
    /**
     * Reference to the Order instance associated with this event.
     */
    OrderRef objectRef,
    /**
     * State before transition (created).
     */
    @NotNull OrderState fromState,
    /**
     * State after transition (approved).
     */
    @NotNull OrderState toState
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef objectRef;
        private OrderState fromState;
        private OrderState toState;

        public Builder objectRef(OrderRef value) {
            this.objectRef = value;
            return this;
        }

        public Builder fromState(OrderState value) {
            this.fromState = value;
            return this;
        }

        public Builder toState(OrderState value) {
            this.toState = value;
            return this;
        }
        public OrderApprovedTransition build() {
            return new OrderApprovedTransition(
                objectRef,
                fromState,
                toState
            );
        }
    }
}
