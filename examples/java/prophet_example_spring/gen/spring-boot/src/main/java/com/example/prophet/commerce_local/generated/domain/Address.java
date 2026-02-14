package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record Address(
    @NotNull String line1,
    @NotNull String city,
    @NotNull String countryCode
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String line1;
        private String city;
        private String countryCode;

        public Builder line1(String value) {
            this.line1 = value;
            return this;
        }

        public Builder city(String value) {
            this.city = value;
            return this;
        }

        public Builder countryCode(String value) {
            this.countryCode = value;
            return this;
        }
        public Address build() {
            return new Address(
                line1,
                city,
                countryCode
            );
        }
    }
}
