package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ShipOrderResult(
    List<List<String>> labelBatches,
    List<String> labels,
    @NotNull String orderId,
    @NotNull String shipmentStatus
) {
}
