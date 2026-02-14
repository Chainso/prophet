package com.example.prophet.generated.actions.handlers.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.ApproveOrderCommand;
import com.example.prophet.generated.actions.ApproveOrderResult;
import com.example.prophet.generated.actions.handlers.ApproveOrderActionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(ApproveOrderActionHandler.class)
@Generated("prophet-cli")
public class ApproveOrderActionHandlerDefault implements ApproveOrderActionHandler {
    @Override
    public ApproveOrderResult handle(ApproveOrderCommand request) {
        throw new UnsupportedOperationException("Action 'approveOrder' is not implemented");
    }
}
