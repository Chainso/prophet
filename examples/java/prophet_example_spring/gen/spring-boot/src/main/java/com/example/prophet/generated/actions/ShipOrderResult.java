package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderResult(
    @NotNull String orderId,
    @NotNull String shipmentStatus,
    List<String> labels,
    List<List<String>> labelBatches
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String shipmentStatus;
        private List<String> labels;
        private List<List<String>> labelBatches;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }

        public Builder shipmentStatus(String value) {
            this.shipmentStatus = value;
            return this;
        }

        public Builder labels(List<String> value) {
            this.labels = value;
            return this;
        }

        public Builder labelBatches(List<List<String>> value) {
            this.labelBatches = value;
            return this;
        }
        public ShipOrderResult build() {
            return new ShipOrderResult(
                orderId,
                shipmentStatus,
                labels,
                labelBatches
            );
        }
    }
}
