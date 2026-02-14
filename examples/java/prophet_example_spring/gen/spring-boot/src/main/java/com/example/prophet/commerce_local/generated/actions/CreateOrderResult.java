package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record CreateOrderResult(
    @NotNull String orderId,
    @NotNull String currentState
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String currentState;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }

        public Builder currentState(String value) {
            this.currentState = value;
            return this;
        }
        public CreateOrderResult build() {
            return new CreateOrderResult(
                orderId,
                currentState
            );
        }
    }
}
