package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record CreateOrderResult(
    @NotNull OrderRef order,
    @NotNull String currentState
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef order;
        private String currentState;

        public Builder order(OrderRef value) {
            this.order = value;
            return this;
        }

        public Builder currentState(String value) {
            this.currentState = value;
            return this;
        }
        public CreateOrderResult build() {
            return new CreateOrderResult(
                order,
                currentState
            );
        }
    }
}
