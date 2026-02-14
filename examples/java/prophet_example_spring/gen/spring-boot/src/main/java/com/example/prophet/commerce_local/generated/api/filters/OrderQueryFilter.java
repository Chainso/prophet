package com.example.prophet.commerce_local.generated.api.filters;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.api.filters.OrderCurrentStateFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderCustomerFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderDiscountCodeFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderOrderIdFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderTotalAmountFilter;

@Generated("prophet-cli")
public record OrderQueryFilter(
    OrderOrderIdFilter orderId,
    OrderCustomerFilter customer,
    OrderTotalAmountFilter totalAmount,
    OrderDiscountCodeFilter discountCode,
    OrderCurrentStateFilter currentState
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderOrderIdFilter orderId;
        private OrderCustomerFilter customer;
        private OrderTotalAmountFilter totalAmount;
        private OrderDiscountCodeFilter discountCode;
        private OrderCurrentStateFilter currentState;

        public Builder orderId(OrderOrderIdFilter value) {
            this.orderId = value;
            return this;
        }

        public Builder customer(OrderCustomerFilter value) {
            this.customer = value;
            return this;
        }

        public Builder totalAmount(OrderTotalAmountFilter value) {
            this.totalAmount = value;
            return this;
        }

        public Builder discountCode(OrderDiscountCodeFilter value) {
            this.discountCode = value;
            return this;
        }

        public Builder currentState(OrderCurrentStateFilter value) {
            this.currentState = value;
            return this;
        }
        public OrderQueryFilter build() {
            return new OrderQueryFilter(
                orderId,
                customer,
                totalAmount,
                discountCode,
                currentState
            );
        }
    }
}
