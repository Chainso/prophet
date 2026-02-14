package com.example.prophet.generated.api;

import com.example.prophet.generated.actions.ApproveOrderCommand;
import com.example.prophet.generated.actions.ApproveOrderResult;
import com.example.prophet.generated.actions.ShipOrderCommand;
import com.example.prophet.generated.actions.ShipOrderResult;
import com.example.prophet.generated.actions.handlers.ApproveOrderActionHandler;
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
public class ActionEndpointController {

    private final ObjectProvider<ApproveOrderActionHandler> approveOrderHandlerProvider;
    private final ObjectProvider<ShipOrderActionHandler> shipOrderHandlerProvider;

    public ActionEndpointController(
        ObjectProvider<ApproveOrderActionHandler> approveOrderHandlerProvider,
        ObjectProvider<ShipOrderActionHandler> shipOrderHandlerProvider
    ) {
        this.approveOrderHandlerProvider = approveOrderHandlerProvider;
        this.shipOrderHandlerProvider = shipOrderHandlerProvider;
    }

    @PostMapping("/approveOrder")
    public ResponseEntity<ApproveOrderResult> approveOrder(@Valid @RequestBody ApproveOrderCommand request) {
        ApproveOrderActionHandler handler = approveOrderHandlerProvider.getIfAvailable();
        if (handler == null) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, "No handler bean provided for action 'approveOrder'");
        }
        return ResponseEntity.ok(handler.handle(request));
    }

    @PostMapping("/shipOrder")
    public ResponseEntity<ShipOrderResult> shipOrder(@Valid @RequestBody ShipOrderCommand request) {
        ShipOrderActionHandler handler = shipOrderHandlerProvider.getIfAvailable();
        if (handler == null) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, "No handler bean provided for action 'shipOrder'");
        }
        return ResponseEntity.ok(handler.handle(request));
    }
}
