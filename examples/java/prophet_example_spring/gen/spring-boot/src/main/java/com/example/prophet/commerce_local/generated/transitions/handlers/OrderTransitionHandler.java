package com.example.prophet.commerce_local.generated.transitions.handlers;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransitionDraft;
import com.example.prophet.commerce_local.generated.events.OrderShipTransitionDraft;

@Generated("prophet-cli")
public interface OrderTransitionHandler {
    OrderApproveTransitionDraft approveOrder(OrderRefOrObject target);
    OrderShipTransitionDraft shipOrder(OrderRefOrObject target);
}
