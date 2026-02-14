package com.example.prophet.generated.actions;

import com.example.prophet.generated.domain.ApprovalContext;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record ApproveOrderCommand(
    String approvedBy,
    ApprovalContext context,
    List<String> notes,
    @NotNull String orderId
) {
}
