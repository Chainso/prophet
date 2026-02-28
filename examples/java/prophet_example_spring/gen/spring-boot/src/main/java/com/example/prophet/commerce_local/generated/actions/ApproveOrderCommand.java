package com.example.prophet.commerce_local.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.ApprovalContext;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/**
 * Input payload for approving an order.
 */
@Generated("prophet-cli")
public record ApproveOrderCommand(
    /**
     * Order that should be approved.
     */
    @NotNull OrderRef order,
    /**
     * Optional user reference for who approved the order.
     */
    UserRef approvedBy,
    /**
     * Optional notes captured as part of approval.
     */
    List<String> notes,
    /**
     * Optional structured context for approval decisions.
     */
    ApprovalContext context
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderRef order;
        private UserRef approvedBy;
        private List<String> notes;
        private ApprovalContext context;

        public Builder order(OrderRef value) {
            this.order = value;
            return this;
        }

        public Builder approvedBy(UserRef value) {
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
                order,
                approvedBy,
                notes,
                context
            );
        }
    }
}
