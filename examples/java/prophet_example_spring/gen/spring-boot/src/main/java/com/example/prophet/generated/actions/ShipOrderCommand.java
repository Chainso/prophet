package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderCommand(
    @NotNull String orderId,
    @NotNull String carrier,
    @NotNull String trackingNumber,
    @NotNull List<String> packageIds
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String carrier;
        private String trackingNumber;
        private List<String> packageIds;

        public Builder orderId(String value) {
            this.orderId = value;
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
                orderId,
                carrier,
                trackingNumber,
                packageIds
            );
        }
    }
}
