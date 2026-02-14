package com.example.prophet.generated.domain;

import com.example.prophet.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record ApprovalContext(
    @NotNull UserRef approver,
    String reason,
    List<UserRef> watchers
) {
}
