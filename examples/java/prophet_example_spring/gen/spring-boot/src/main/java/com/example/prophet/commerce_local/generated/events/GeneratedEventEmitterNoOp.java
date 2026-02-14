package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(value = GeneratedEventEmitter.class, ignored = GeneratedEventEmitterNoOp.class)
@Generated("prophet-cli")
public class GeneratedEventEmitterNoOp implements GeneratedEventEmitter {
    @Override
    public void emitOrderApprovedEvent(OrderApprovedEvent event) {
    }

    @Override
    public void emitOrderApprovedTransition(OrderApprovedTransition event) {
    }

    @Override
    public void emitOrderCreatedEvent(OrderCreatedEvent event) {
    }

    @Override
    public void emitOrderShippedEvent(OrderShippedEvent event) {
    }

    @Override
    public void emitPaymentCaptured(PaymentCaptured event) {
    }

}
