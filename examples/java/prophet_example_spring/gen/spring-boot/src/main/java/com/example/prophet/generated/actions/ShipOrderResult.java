package com.example.prophet.generated.actions;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record ShipOrderResult(
    List<List<String>> labelBatches,
    List<String> labels,
    @NotNull String orderId,
    @NotNull String shipmentStatus
) {
}
