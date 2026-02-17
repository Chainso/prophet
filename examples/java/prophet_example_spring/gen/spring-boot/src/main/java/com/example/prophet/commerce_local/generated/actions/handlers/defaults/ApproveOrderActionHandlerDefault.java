package com.example.prophet.commerce_local.generated.actions.handlers.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(ApproveOrderActionHandler.class)
@Generated("prophet-cli")
public class ApproveOrderActionHandlerDefault implements ApproveOrderActionHandler {
    @Override
    public OrderApproveTransition handle(ApproveOrderCommand request) {
        throw new UnsupportedOperationException("Action 'approveOrder' is not implemented");
    }
}
