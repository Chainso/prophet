package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Platform user who can place or approve orders.
 */
@Generated("prophet-cli")
public record User(
    /**
     * Stable user identifier.
     */
    @NotNull String userId,
    /**
     * Email address used to contact the user.
     */
    @NotNull String email
) implements UserRefOrObject {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String userId;
        private String email;

        public Builder userId(String value) {
            this.userId = value;
            return this;
        }

        public Builder email(String value) {
            this.email = value;
            return this;
        }
        public User build() {
            return new User(
                userId,
                email
            );
        }
    }
}
