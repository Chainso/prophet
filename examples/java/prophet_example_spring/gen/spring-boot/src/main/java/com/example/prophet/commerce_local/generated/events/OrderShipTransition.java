package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Event payload for 'OrderShipTransition'.
 */
@Generated("prophet-cli")
public record OrderShipTransition(
    @NotNull String orderId,
    @NotNull String fromState,
    @NotNull String toState
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String fromState;
        private String toState;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }

        public Builder fromState(String value) {
            this.fromState = value;
            return this;
        }

        public Builder toState(String value) {
            this.toState = value;
            return this;
        }
        public OrderShipTransition build() {
            return new OrderShipTransition(
                orderId,
                fromState,
                toState
            );
        }
    }
}
