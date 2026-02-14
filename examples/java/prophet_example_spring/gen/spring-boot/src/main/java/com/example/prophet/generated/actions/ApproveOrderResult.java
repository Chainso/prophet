package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApproveOrderResult(
    @NotNull String decision,
    @NotNull String orderId,
    List<String> warnings
) {
}
