package com.example.prophet_example_spring.actions;

import com.example.prophet.commerce_local.generated.actions.ApproveOrderCommand;
import com.example.prophet.commerce_local.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.commerce_local.generated.domain.OrderRef;
import com.example.prophet.commerce_local.generated.domain.OrderStatus;
import com.example.prophet.commerce_local.generated.events.OrderApproved;
import com.example.prophet.commerce_local.generated.persistence.OrderEntity;
import com.example.prophet.commerce_local.generated.persistence.OrderRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Component
public class ApproveOrderHandler implements ApproveOrderActionHandler {

    private final OrderRepository orderRepository;

    public ApproveOrderHandler(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @Override
    @Transactional
    public OrderApproved handle(ApproveOrderCommand request) {
        OrderEntity order = orderRepository.findById(request.order().orderId())
            .orElseThrow(() -> new IllegalArgumentException("order not found: " + request.order().orderId()));

        List<String> notes = request.notes() == null ? List.of() : request.notes();
        String approvalReason = request.context() != null ? request.context().reason() : null;

        order.setApprovedByUserId(request.approvedBy() == null ? null : request.approvedBy().userId());
        order.setApprovalNotes(notes);
        order.setApprovalReason(approvalReason);
        order.setStatus(OrderStatus.Approved);
        order = orderRepository.save(order);

        return OrderApproved.builder()
            .order(OrderRef.builder().orderId(order.getOrderId()).build())
            .build();
    }
}
