package com.example.prophet.generated.actions;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record ShipOrderCommand(
    @NotNull String carrier,
    @NotNull String orderId,
    @NotNull List<String> packageIds,
    @NotNull String trackingNumber
) {
}
