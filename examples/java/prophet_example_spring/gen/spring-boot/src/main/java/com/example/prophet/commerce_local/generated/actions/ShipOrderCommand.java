package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/**
 * Input payload for shipping an approved order.
 */
@Generated("prophet-cli")
public record ShipOrderCommand(
    /**
     * Approved order that should be shipped.
     */
    @NotNull OrderRef order,
    /**
     * Carrier service selected for shipment.
     */
    @NotNull String carrier,
    /**
     * Tracking number assigned by the carrier.
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
        private OrderRef order;
        private String carrier;
        private String trackingNumber;
        private List<String> packageIds;

        public Builder order(OrderRef value) {
            this.order = value;
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
        public ShipOrderCommand build() {
            return new ShipOrderCommand(
                order,
                carrier,
                trackingNumber,
                packageIds
            );
        }
    }
}
