package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record User(
    @NotNull String userId,
    @NotNull String email
) {

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
