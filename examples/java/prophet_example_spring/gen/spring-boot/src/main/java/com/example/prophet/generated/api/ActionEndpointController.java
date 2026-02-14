package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.ApproveOrderCommand;
import com.example.prophet.generated.actions.ApproveOrderResult;
import com.example.prophet.generated.actions.CreateOrderCommand;
import com.example.prophet.generated.actions.CreateOrderResult;
import com.example.prophet.generated.actions.ShipOrderCommand;
import com.example.prophet.generated.actions.ShipOrderResult;
import com.example.prophet.generated.actions.handlers.ApproveOrderActionHandler;
import com.example.prophet.generated.actions.handlers.CreateOrderActionHandler;
import com.example.prophet.generated.actions.handlers.ShipOrderActionHandler;
import jakarta.validation.Valid;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import static org.springframework.http.HttpStatus.NOT_IMPLEMENTED;

@RestController
@RequestMapping("/actions")
@Generated("prophet-cli")
public class ActionEndpointController {

    private final ObjectProvider<ApproveOrderActionHandler> approveOrderHandlerProvider;
    private final ObjectProvider<CreateOrderActionHandler> createOrderHandlerProvider;
    private final ObjectProvider<ShipOrderActionHandler> shipOrderHandlerProvider;

    public ActionEndpointController(
        ObjectProvider<ApproveOrderActionHandler> approveOrderHandlerProvider,
        ObjectProvider<CreateOrderActionHandler> createOrderHandlerProvider,
        ObjectProvider<ShipOrderActionHandler> shipOrderHandlerProvider
    ) {
        this.approveOrderHandlerProvider = approveOrderHandlerProvider;
        this.createOrderHandlerProvider = createOrderHandlerProvider;
        this.shipOrderHandlerProvider = shipOrderHandlerProvider;
    }

    @PostMapping("/approveOrder")
    public ResponseEntity<ApproveOrderResult> approveOrder(@Valid @RequestBody ApproveOrderCommand request) {
        ApproveOrderActionHandler handler = approveOrderHandlerProvider.getIfAvailable();
        if (handler == null) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, "No handler bean provided for action 'approveOrder'");
        }
        try {
            return ResponseEntity.ok(handler.handle(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }

    @PostMapping("/createOrder")
    public ResponseEntity<CreateOrderResult> createOrder(@Valid @RequestBody CreateOrderCommand request) {
        CreateOrderActionHandler handler = createOrderHandlerProvider.getIfAvailable();
        if (handler == null) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, "No handler bean provided for action 'createOrder'");
        }
        try {
            return ResponseEntity.ok(handler.handle(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }

    @PostMapping("/shipOrder")
    public ResponseEntity<ShipOrderResult> shipOrder(@Valid @RequestBody ShipOrderCommand request) {
        ShipOrderActionHandler handler = shipOrderHandlerProvider.getIfAvailable();
        if (handler == null) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, "No handler bean provided for action 'shipOrder'");
        }
        try {
            return ResponseEntity.ok(handler.handle(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }
}
