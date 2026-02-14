package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;

@Generated("prophet-cli")
public record CreateOrderResult(
    @NotNull String currentState,
    @NotNull String orderId
) {
}
