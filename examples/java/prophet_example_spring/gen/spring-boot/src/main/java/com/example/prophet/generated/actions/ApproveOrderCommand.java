package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.ApprovalContext;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApproveOrderCommand(
    @NotNull String orderId,
    String approvedBy,
    List<String> notes,
    ApprovalContext context
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String approvedBy;
        private List<String> notes;
        private ApprovalContext context;

        public Builder orderId(String value) {
            this.orderId = value;
            return this;
        }

        public Builder approvedBy(String value) {
            this.approvedBy = value;
            return this;
        }

        public Builder notes(List<String> value) {
            this.notes = value;
            return this;
        }

        public Builder context(ApprovalContext value) {
            this.context = value;
            return this;
        }
        public ApproveOrderCommand build() {
            return new ApproveOrderCommand(
                orderId,
                approvedBy,
                notes,
                context
            );
        }
    }
}
