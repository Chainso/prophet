package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderCommand(
    @NotNull String carrier,
    @NotNull String orderId,
    @NotNull List<String> packageIds,
    @NotNull String trackingNumber
) {
}
