package com.example.prophet.generated.api.filters;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.api.filters.UserEmailFilter;
import com.example.prophet.generated.api.filters.UserUserIdFilter;

@Generated("prophet-cli")
public record UserQueryFilter(
    UserUserIdFilter userId,
    UserEmailFilter email
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private UserUserIdFilter userId;
        private UserEmailFilter email;

        public Builder userId(UserUserIdFilter value) {
            this.userId = value;
            return this;
        }

        public Builder email(UserEmailFilter value) {
            this.email = value;
            return this;
        }
        public UserQueryFilter build() {
            return new UserQueryFilter(
                userId,
                email
            );
        }
    }
}
