package com.example.prophet.commerce_local.generated.api.filters;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.api.filters.OrderApprovalReasonFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderApprovedByUserIdFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderCustomerFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderDiscountCodeFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderOrderIdFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderShippingCarrierFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderShippingTrackingNumberFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderStateFilter;
import com.example.prophet.commerce_local.generated.api.filters.OrderTotalAmountFilter;

@Generated("prophet-cli")
public record OrderQueryFilter(
    OrderOrderIdFilter orderId,
    OrderCustomerFilter customer,
    OrderTotalAmountFilter totalAmount,
    OrderDiscountCodeFilter discountCode,
    OrderApprovedByUserIdFilter approvedByUserId,
    OrderApprovalReasonFilter approvalReason,
    OrderShippingCarrierFilter shippingCarrier,
    OrderShippingTrackingNumberFilter shippingTrackingNumber,
    OrderStateFilter state
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderOrderIdFilter orderId;
        private OrderCustomerFilter customer;
        private OrderTotalAmountFilter totalAmount;
        private OrderDiscountCodeFilter discountCode;
        private OrderApprovedByUserIdFilter approvedByUserId;
        private OrderApprovalReasonFilter approvalReason;
        private OrderShippingCarrierFilter shippingCarrier;
        private OrderShippingTrackingNumberFilter shippingTrackingNumber;
        private OrderStateFilter state;

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

        public Builder approvedByUserId(OrderApprovedByUserIdFilter value) {
            this.approvedByUserId = value;
            return this;
        }

        public Builder approvalReason(OrderApprovalReasonFilter value) {
            this.approvalReason = value;
            return this;
        }

        public Builder shippingCarrier(OrderShippingCarrierFilter value) {
            this.shippingCarrier = value;
            return this;
        }

        public Builder shippingTrackingNumber(OrderShippingTrackingNumberFilter value) {
            this.shippingTrackingNumber = value;
            return this;
        }

        public Builder state(OrderStateFilter value) {
            this.state = value;
            return this;
        }
        public OrderQueryFilter build() {
            return new OrderQueryFilter(
                orderId,
                customer,
                totalAmount,
                discountCode,
                approvedByUserId,
                approvalReason,
                shippingCarrier,
                shippingTrackingNumber,
                state
            );
        }
    }
}
