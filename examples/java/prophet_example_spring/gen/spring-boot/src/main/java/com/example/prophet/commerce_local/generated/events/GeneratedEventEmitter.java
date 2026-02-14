package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.events.OrderApprovedEvent;
import com.example.prophet.commerce_local.generated.events.OrderApprovedTransition;
import com.example.prophet.commerce_local.generated.events.OrderCreatedEvent;
import com.example.prophet.commerce_local.generated.events.OrderShippedEvent;
import com.example.prophet.commerce_local.generated.events.PaymentCaptured;

@Generated("prophet-cli")
public interface GeneratedEventEmitter {
    /**
     * Emit 'OrderApprovedEvent'.
     */
    void emitOrderApprovedEvent(OrderApprovedEvent event);

    /**
     * Emit 'OrderApprovedTransition'.
     */
    void emitOrderApprovedTransition(OrderApprovedTransition event);

    /**
     * Emit 'OrderCreatedEvent'.
     */
    void emitOrderCreatedEvent(OrderCreatedEvent event);

    /**
     * Emit 'OrderShippedEvent'.
     */
    void emitOrderShippedEvent(OrderShippedEvent event);

    /**
     * Emit 'PaymentCaptured'.
     */
    void emitPaymentCaptured(PaymentCaptured event);

}
