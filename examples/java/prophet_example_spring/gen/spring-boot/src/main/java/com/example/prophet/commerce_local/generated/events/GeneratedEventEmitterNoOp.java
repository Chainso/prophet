package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.events.PaymentCaptured;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(value = GeneratedEventEmitter.class, ignored = GeneratedEventEmitterNoOp.class)
@Generated("prophet-cli")
public class GeneratedEventEmitterNoOp implements GeneratedEventEmitter {
    @Override
    public void emitApproveOrderResult(ApproveOrderResult event) {
    }

    @Override
    public void emitCreateOrderResult(CreateOrderResult event) {
    }

    @Override
    public void emitShipOrderResult(ShipOrderResult event) {
    }

    @Override
    public void emitPaymentCaptured(PaymentCaptured event) {
    }

    @Override
    public void emitOrderApproveTransition(OrderApproveTransition event) {
    }

    @Override
    public void emitOrderShipTransition(OrderShipTransition event) {
    }

}
