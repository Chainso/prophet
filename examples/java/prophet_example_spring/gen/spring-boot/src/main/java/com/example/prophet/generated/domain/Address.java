package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record Address(
    @NotNull String city,
    @NotNull String countryCode,
    @NotNull String line1
) {
}
