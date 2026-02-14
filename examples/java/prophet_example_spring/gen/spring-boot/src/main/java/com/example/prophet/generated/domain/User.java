package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record User(
    @NotNull String email,
    @NotNull String userId
) {
}
