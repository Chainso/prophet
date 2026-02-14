package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.ApprovalContext;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApproveOrderCommand(
    @NotNull String orderId,
    String approvedBy,
    List<String> notes,
    ApprovalContext context
) {
}
