package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record ApprovalContext(
    @NotNull UserRef approver,
    String reason,
    List<UserRef> watchers
) {
}
