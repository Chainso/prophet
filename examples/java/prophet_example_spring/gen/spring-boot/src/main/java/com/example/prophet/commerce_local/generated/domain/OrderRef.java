package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Reference to Order by primary key.
 */
@Generated("prophet-cli")
public record OrderRef(
    /**
     * Primary key for referenced Order.
     */
    @NotNull String orderId
) implements OrderRefOrObject {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }
        public OrderRef build() {
            return new OrderRef(
                orderId
            );
        }
    }
}
