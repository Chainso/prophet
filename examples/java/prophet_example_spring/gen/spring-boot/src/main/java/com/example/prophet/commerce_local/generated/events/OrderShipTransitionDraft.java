package com.example.prophet.commerce_local.generated.events;

public final class OrderShipTransitionDraft {
    private final OrderShipTransition.Builder builder;

    public OrderShipTransitionDraft(OrderShipTransition.Builder builder) {
        this.builder = builder;
    }

    public OrderShipTransition.Builder builder() {
        return builder;
    }

    public OrderShipTransition build() {
        return builder.build();
    }
}
