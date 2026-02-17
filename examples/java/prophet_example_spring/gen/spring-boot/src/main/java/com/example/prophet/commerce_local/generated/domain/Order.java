package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Address;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

/**
 * Customer order aggregate.
 */
@Generated("prophet-cli")
public record Order(
    /**
     * Stable order identifier.
     */
    @NotNull String orderId,
    @NotNull UserRef customer,
    @NotNull BigDecimal totalAmount,
    String discountCode,
    List<String> tags,
    Address shippingAddress,
    @NotNull OrderState currentState
) implements OrderRefOrObject {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private UserRef customer;
        private BigDecimal totalAmount;
        private String discountCode;
        private List<String> tags;
        private Address shippingAddress;
        private OrderState currentState;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }

        public Builder customer(UserRef value) {
            this.customer = value;
            return this;
        }

        public Builder totalAmount(BigDecimal value) {
            this.totalAmount = value;
            return this;
        }

        public Builder discountCode(String value) {
            this.discountCode = value;
            return this;
        }

        public Builder tags(List<String> value) {
            this.tags = value;
            return this;
        }

        public Builder shippingAddress(Address value) {
            this.shippingAddress = value;
            return this;
        }

        public Builder currentState(OrderState value) {
            this.currentState = value;
            return this;
        }
        public Order build() {
            return new Order(
                orderId,
                customer,
                totalAmount,
                discountCode,
                tags,
                shippingAddress,
                currentState
            );
        }
    }
}
