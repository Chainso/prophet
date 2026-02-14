package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApproveOrderResult(
    @NotNull String orderId,
    @NotNull String decision,
    List<String> warnings
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String decision;
        private List<String> warnings;

        public Builder orderId(String value) {
            this.orderId = value;
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
                orderId,
                decision,
                warnings
            );
        }
    }
}
