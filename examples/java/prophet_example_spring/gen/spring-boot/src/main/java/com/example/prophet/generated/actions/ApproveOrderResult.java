package com.example.prophet.generated.actions;

import jakarta.validation.constraints.NotNull;
import java.util.List;

public record ApproveOrderResult(
    @NotNull String decision,
    @NotNull String orderId,
    List<String> warnings
) {
}
