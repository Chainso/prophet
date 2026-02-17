package com.example.prophet.commerce_local.generated.transitions.services;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransitionDraft;
import com.example.prophet.commerce_local.generated.events.OrderShipTransitionDraft;

@Generated("prophet-cli")
public interface OrderTransitionService {
    OrderApproveTransitionDraft approveOrder(OrderRefOrObject target);
    OrderShipTransitionDraft shipOrder(OrderRefOrObject target);
}
