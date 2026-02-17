package com.example.prophet.commerce_local.generated.events;

public sealed interface DomainEvent permits CreateOrderResultEvent, PaymentCapturedEvent, OrderApproveTransitionEvent, OrderShipTransitionEvent {
}
