package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

/**
 * Postal address used for shipping destinations.
 */
@Generated("prophet-cli")
public record Address(
    /**
     * Primary street address line.
     */
    @NotNull String line1,
    /**
     * City or locality for the address.
     */
    @NotNull String city,
    /**
     * Country code representing the destination nation.
     */
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
