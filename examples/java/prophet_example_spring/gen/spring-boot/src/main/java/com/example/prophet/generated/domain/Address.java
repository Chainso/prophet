package com.example.prophet.generated.domain;

import jakarta.validation.constraints.NotNull;

public record Address(
    @NotNull String city,
    @NotNull String countryCode,
    @NotNull String line1
) {
}
