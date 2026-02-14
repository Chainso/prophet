package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record UserRef(
    @NotNull String userId
) {

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
