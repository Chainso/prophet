package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderResult(
    @NotNull OrderRef order,
    @NotNull String shipmentStatus,
    List<String> labels,
    List<List<String>> labelBatches
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef order;
        private String shipmentStatus;
        private List<String> labels;
        private List<List<String>> labelBatches;

        public Builder order(OrderRef value) {
            this.order = value;
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
                order,
                shipmentStatus,
                labels,
                labelBatches
            );
        }
    }
}
