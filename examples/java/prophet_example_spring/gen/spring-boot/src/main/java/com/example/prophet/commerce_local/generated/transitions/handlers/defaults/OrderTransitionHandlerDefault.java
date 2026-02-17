package com.example.prophet.commerce_local.generated.transitions.handlers.defaults;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Order;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderRefOrObject;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransitionDraft;
import com.example.prophet.commerce_local.generated.events.OrderShipTransition;
import com.example.prophet.commerce_local.generated.events.OrderShipTransitionDraft;
import com.example.prophet.commerce_local.generated.mapping.OrderDomainMapper;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import com.example.prophet.commerce_local.generated.persistence.OrderStateHistoryEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderStateHistoryRepository;
import com.example.prophet.commerce_local.generated.transitions.handlers.OrderTransitionHandler;
import com.example.prophet.commerce_local.generated.transitions.validators.OrderTransitionValidator;
import io.prophet.events.runtime.TransitionValidationResult;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnMissingBean(value = OrderTransitionHandler.class, ignored = OrderTransitionHandlerDefault.class)
@Generated("prophet-cli")
public class OrderTransitionHandlerDefault implements OrderTransitionHandler {
    private final OrderRepository repository;
    private final OrderDomainMapper mapper;
    private final OrderTransitionValidator validator;
    private final OrderStateHistoryRepository historyRepository;

    public OrderTransitionHandlerDefault(
        OrderRepository repository,
        OrderDomainMapper mapper,
        OrderTransitionValidator validator,
        OrderStateHistoryRepository historyRepository
    ) {
        this.repository = repository;
        this.mapper = mapper;
        this.validator = validator;
        this.historyRepository = historyRepository;
    }

    @Override
    public OrderApproveTransitionDraft approveOrder(OrderRefOrObject target) {
        var orderId = target instanceof OrderRef ref ? ref.orderId() : ((Order) target).orderId();
        OrderEntity entity = repository.findById(orderId)
            .orElseThrow(() -> new IllegalStateException("Order not found for transition 'approve'"));
        if (entity.getState() != OrderState.CREATED) {
            throw new IllegalStateException("Invalid state transition Order.approve: expected created but was " + entity.getState());
        }
        Order current = mapper.toDomain(entity);
        TransitionValidationResult validation = validator.validateApproveOrder(current);
        if (!validation.passesValidation()) {
            throw new IllegalStateException(validation.failureReason() == null || validation.failureReason().isBlank() ? "Transition validation failed for Order.approve" : validation.failureReason());
        }
        entity.setState(OrderState.APPROVED);
        entity = repository.save(entity);
        OrderStateHistoryEntity history = new OrderStateHistoryEntity();
        history.setOrder(entity);
        history.setTransitionId("trans_order_approve");
        history.setFromState("created");
        history.setToState("approved");
        historyRepository.save(history);
        OrderApproveTransition.Builder builder = OrderApproveTransition.builder()
            .orderId(orderId)
            .fromState("created")
            .toState("approved");
        return new OrderApproveTransitionDraft(builder);
    }

    @Override
    public OrderShipTransitionDraft shipOrder(OrderRefOrObject target) {
        var orderId = target instanceof OrderRef ref ? ref.orderId() : ((Order) target).orderId();
        OrderEntity entity = repository.findById(orderId)
            .orElseThrow(() -> new IllegalStateException("Order not found for transition 'ship'"));
        if (entity.getState() != OrderState.APPROVED) {
            throw new IllegalStateException("Invalid state transition Order.ship: expected approved but was " + entity.getState());
        }
        Order current = mapper.toDomain(entity);
        TransitionValidationResult validation = validator.validateShipOrder(current);
        if (!validation.passesValidation()) {
            throw new IllegalStateException(validation.failureReason() == null || validation.failureReason().isBlank() ? "Transition validation failed for Order.ship" : validation.failureReason());
        }
        entity.setState(OrderState.SHIPPED);
        entity = repository.save(entity);
        OrderStateHistoryEntity history = new OrderStateHistoryEntity();
        history.setOrder(entity);
        history.setTransitionId("trans_order_ship");
        history.setFromState("approved");
        history.setToState("shipped");
        historyRepository.save(history);
        OrderShipTransition.Builder builder = OrderShipTransition.builder()
            .orderId(orderId)
            .fromState("approved")
            .toState("shipped");
        return new OrderShipTransitionDraft(builder);
    }
}
