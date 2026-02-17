package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Reference to User by primary key.
 */
@Generated("prophet-cli")
public record UserRef(
    /**
     * Primary key for referenced User.
     */
    @NotNull String userId
) implements UserRefOrObject {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String userId;

        public Builder userId(String value) {
            this.userId = value;
            return this;
        }
        public UserRef build() {
            return new UserRef(
                userId
            );
        }
    }
}
