package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApprovalContext(
    @NotNull UserRef approver,
    List<UserRef> watchers,
    String reason
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private UserRef approver;
        private List<UserRef> watchers;
        private String reason;

        public Builder approver(UserRef value) {
            this.approver = value;
            return this;
        }

        public Builder watchers(List<UserRef> value) {
            this.watchers = value;
            return this;
        }

        public Builder reason(String value) {
            this.reason = value;
            return this;
        }
        public ApprovalContext build() {
            return new ApprovalContext(
                approver,
                watchers,
                reason
            );
        }
    }
}
