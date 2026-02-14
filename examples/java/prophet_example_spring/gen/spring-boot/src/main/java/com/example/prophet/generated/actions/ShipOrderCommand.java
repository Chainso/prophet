package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderCommand(
    @NotNull String orderId,
    @NotNull String carrier,
    @NotNull String trackingNumber,
    @NotNull List<String> packageIds
) {
}
