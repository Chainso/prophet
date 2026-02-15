package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import java.util.List;

@Generated("prophet-cli")
public record ActionOutcome<T>(T output, List<DomainEvent> additionalEvents) {
    public ActionOutcome {
        additionalEvents = additionalEvents == null ? List.of() : List.copyOf(additionalEvents);
    }
}
