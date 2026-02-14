package com.example.prophet.generated.domain;

import jakarta.validation.constraints.NotNull;

public record User(
    @NotNull String email,
    @NotNull String userId
) {
}
