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
    /**
     * Reference to the user who placed the order.
     */
    @NotNull UserRef customer,
    /**
     * Total monetary amount recorded for the order.
     */
    @NotNull BigDecimal totalAmount,
    /**
     * Optional promotional code applied during checkout.
     */
    String discountCode,
    /**
     * Optional labels used for filtering and analytics.
     */
    List<String> tags,
    /**
     * Optional destination address for order fulfillment.
     */
    Address shippingAddress,
    /**
     * Optional identifier of the user who approved the order.
     */
    String approvedByUserId,
    /**
     * Optional notes captured while approving the order.
     */
    List<String> approvalNotes,
    /**
     * Optional reason recorded for the approval decision.
     */
    String approvalReason,
    /**
     * Optional carrier name used for shipment.
     */
    String shippingCarrier,
    /**
     * Optional tracking number assigned by the carrier.
     */
    String shippingTrackingNumber,
    /**
     * Optional identifiers for packages in the shipment.
     */
    List<String> shippingPackageIds,
    @NotNull OrderState state
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
        private String approvedByUserId;
        private List<String> approvalNotes;
        private String approvalReason;
        private String shippingCarrier;
        private String shippingTrackingNumber;
        private List<String> shippingPackageIds;
        private OrderState state;

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

        public Builder approvedByUserId(String value) {
            this.approvedByUserId = value;
            return this;
        }

        public Builder approvalNotes(List<String> value) {
            this.approvalNotes = value;
            return this;
        }

        public Builder approvalReason(String value) {
            this.approvalReason = value;
            return this;
        }

        public Builder shippingCarrier(String value) {
            this.shippingCarrier = value;
            return this;
        }

        public Builder shippingTrackingNumber(String value) {
            this.shippingTrackingNumber = value;
            return this;
        }

        public Builder shippingPackageIds(List<String> value) {
            this.shippingPackageIds = value;
            return this;
        }

        public Builder state(OrderState value) {
            this.state = value;
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
                approvedByUserId,
                approvalNotes,
                approvalReason,
                shippingCarrier,
                shippingTrackingNumber,
                shippingPackageIds,
                state
            );
        }
    }
}
