package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.actions.ApproveOrderCommand;
import com.example.prophet.generated.actions.ApproveOrderResult;
import com.example.prophet.generated.actions.CreateOrderCommand;
import com.example.prophet.generated.actions.CreateOrderResult;
import com.example.prophet.generated.actions.ShipOrderCommand;
import com.example.prophet.generated.actions.ShipOrderResult;
import com.example.prophet.generated.actions.services.ApproveOrderActionService;
import com.example.prophet.generated.actions.services.CreateOrderActionService;
import com.example.prophet.generated.actions.services.ShipOrderActionService;
import jakarta.validation.Valid;
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

    private final ApproveOrderActionService approveOrderService;
    private final CreateOrderActionService createOrderService;
    private final ShipOrderActionService shipOrderService;

    public ActionEndpointController(
        ApproveOrderActionService approveOrderService,
        CreateOrderActionService createOrderService,
        ShipOrderActionService shipOrderService
    ) {
        this.approveOrderService = approveOrderService;
        this.createOrderService = createOrderService;
        this.shipOrderService = shipOrderService;
    }

    @PostMapping("/approveOrder")
    public ResponseEntity<ApproveOrderResult> approveOrder(@Valid @RequestBody ApproveOrderCommand request) {
        try {
            return ResponseEntity.ok(approveOrderService.execute(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }

    @PostMapping("/createOrder")
    public ResponseEntity<CreateOrderResult> createOrder(@Valid @RequestBody CreateOrderCommand request) {
        try {
            return ResponseEntity.ok(createOrderService.execute(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }

    @PostMapping("/shipOrder")
    public ResponseEntity<ShipOrderResult> shipOrder(@Valid @RequestBody ShipOrderCommand request) {
        try {
            return ResponseEntity.ok(shipOrderService.execute(request));
        } catch (UnsupportedOperationException ex) {
            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);
        }
    }
}
