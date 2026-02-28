package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/**
 * Moves an order from approved to shipped.
 */
@Generated("prophet-cli")
public record OrderShipTransition(
    @NotNull String orderId,
    @NotNull String fromState,
    @NotNull String toState,
    /**
     * Carrier service handling shipment delivery.
     */
    @NotNull String carrier,
    /**
     * Tracking reference assigned for the shipment.
     */
    @NotNull String trackingNumber,
    /**
     * Package identifiers included in this shipment.
     */
    @NotNull List<String> packageIds
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String fromState;
        private String toState;
        private String carrier;
        private String trackingNumber;
        private List<String> packageIds;

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

        public Builder carrier(String value) {
            this.carrier = value;
            return this;
        }

        public Builder trackingNumber(String value) {
            this.trackingNumber = value;
            return this;
        }

        public Builder packageIds(List<String> value) {
            this.packageIds = value;
            return this;
        }
        public OrderShipTransition build() {
            return new OrderShipTransition(
                orderId,
                fromState,
                toState,
                carrier,
                trackingNumber,
                packageIds
            );
        }
    }
}
