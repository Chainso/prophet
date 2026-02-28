package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Address;
import com.example.prophet.commerce_local.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

/**
 * Input payload for creating a new order.
 */
@Generated("prophet-cli")
public record CreateOrderCommand(
    /**
     * Customer who is placing the order.
     */
    @NotNull UserRef customer,
    /**
     * Requested total amount for the new order.
     */
    @NotNull BigDecimal totalAmount,
    /**
     * Optional discount code applied to the order.
     */
    String discountCode,
    /**
     * Optional labels attached at order creation.
     */
    List<String> tags,
    /**
     * Optional shipping destination for the order.
     */
    Address shippingAddress
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private UserRef customer;
        private BigDecimal totalAmount;
        private String discountCode;
        private List<String> tags;
        private Address shippingAddress;

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
        public CreateOrderCommand build() {
            return new CreateOrderCommand(
                customer,
                totalAmount,
                discountCode,
                tags,
                shippingAddress
            );
        }
    }
}
