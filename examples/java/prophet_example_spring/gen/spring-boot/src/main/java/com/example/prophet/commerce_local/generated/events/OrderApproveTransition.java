package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Moves an order from created to approved.
 */
@Generated("prophet-cli")
public record OrderApproveTransition(
    @NotNull String orderId,
    @NotNull String fromState,
    @NotNull String toState,
    /**
     * Optional approver identifier captured in the transition.
     */
    String approvedByUserId,
    /**
     * Count of approval notes included with this transition.
     */
    @NotNull Integer noteCount,
    /**
     * Optional reason text supplied for approval.
     */
    String approvalReason
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String orderId;
        private String fromState;
        private String toState;
        private String approvedByUserId;
        private Integer noteCount;
        private String approvalReason;

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

        public Builder approvedByUserId(String value) {
            this.approvedByUserId = value;
            return this;
        }

        public Builder noteCount(Integer value) {
            this.noteCount = value;
            return this;
        }

        public Builder approvalReason(String value) {
            this.approvalReason = value;
            return this;
        }
        public OrderApproveTransition build() {
            return new OrderApproveTransition(
                orderId,
                fromState,
                toState,
                approvedByUserId,
                noteCount,
                approvalReason
            );
        }
    }
}
