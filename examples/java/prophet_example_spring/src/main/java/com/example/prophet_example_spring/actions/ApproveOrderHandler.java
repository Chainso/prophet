package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.commerce_local.generated.events.OrderApproveTransition;
import com.example.prophet.commerce_local.generated.mapping.OrderDomainMapper;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import com.example.prophet.commerce_local.generated.transitions.services.OrderTransitionService;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Component
public class ApproveOrderHandler implements ApproveOrderActionHandler {

    private final OrderRepository orderRepository;
    private final OrderDomainMapper orderDomainMapper;
    private final OrderTransitionService orderTransitionService;

    public ApproveOrderHandler(
        OrderRepository orderRepository,
        OrderDomainMapper orderDomainMapper,
        OrderTransitionService orderTransitionService
    ) {
        this.orderRepository = orderRepository;
        this.orderDomainMapper = orderDomainMapper;
        this.orderTransitionService = orderTransitionService;
    }

    @Override
    @Transactional
    public OrderApproveTransition handle(ApproveOrderCommand request) {
        OrderEntity order = orderRepository.findById(request.order().orderId())
            .orElseThrow(() -> new IllegalArgumentException("order not found: " + request.order().orderId()));

        List<String> notes = request.notes() == null ? List.of() : request.notes();
        String approvalReason = request.context() != null ? request.context().reason() : null;

        order.setApprovedByUserId(request.approvedBy() == null ? null : request.approvedBy().userId());
        order.setApprovalNotes(request.notes());
        order.setApprovalReason(approvalReason);
        order = orderRepository.save(order);

        return orderTransitionService
            .approveOrder(orderDomainMapper.toDomain(order))
            .builder()
            .approvedByUserId(order.getApprovedByUserId())
            .noteCount(notes.size())
            .approvalReason(order.getApprovalReason())
            .build();
    }
}
