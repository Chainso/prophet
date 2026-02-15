package com.example.prophet.commerce_local.generated.events;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderResult;
import com.example.prophet.commerce_local.generated.actions.CreateOrderResult;
import com.example.prophet.commerce_local.generated.actions.ShipOrderResult;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.events.PaymentCaptured;

@Generated("prophet-cli")
public interface GeneratedEventEmitter {
    /**
     * Approval result contract.
     */
    void emitApproveOrderResult(ApproveOrderResult event);

    /**
     * Emit 'CreateOrderResult'.
     */
    void emitCreateOrderResult(CreateOrderResult event);

    /**
     * Emit 'ShipOrderResult'.
     */
    void emitShipOrderResult(ShipOrderResult event);

    /**
     * Emit 'PaymentCaptured'.
     */
    void emitPaymentCaptured(PaymentCaptured event);

    /**
     * Emit 'OrderApproveTransition'.
     */
    void emitOrderApproveTransition(OrderApproveTransition event);

    /**
     * Emit 'OrderShipTransition'.
     */
    void emitOrderShipTransition(OrderShipTransition event);

}
