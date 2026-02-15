package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/**
 * Approval result contract.
 */
@Generated("prophet-cli")
public record ApproveOrderResult(
    @NotNull OrderRef order,
    @NotNull String decision,
    List<String> warnings
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef order;
        private String decision;
        private List<String> warnings;

        public Builder order(OrderRef value) {
            this.order = value;
            return this;
        }

        public Builder decision(String value) {
            this.decision = value;
            return this;
        }

        public Builder warnings(List<String> value) {
            this.warnings = value;
            return this;
        }
        public ApproveOrderResult build() {
            return new ApproveOrderResult(
                order,
                decision,
                warnings
            );
        }
    }
}
