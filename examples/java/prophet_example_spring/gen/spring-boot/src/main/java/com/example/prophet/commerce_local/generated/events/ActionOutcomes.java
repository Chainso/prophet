package com.example.prophet.commerce_local.generated.events;

import java.util.Arrays;
import java.util.List;

public final class ActionOutcomes {
    private ActionOutcomes() {}

    public static <T> ActionOutcome<T> just(T output) {
        return new ActionOutcome<>(output, List.of());
    }

    public static <T> ActionOutcome<T> withEvents(T output, DomainEvent... additionalEvents) {
        return new ActionOutcome<>(output, Arrays.asList(additionalEvents));
    }
}
