package com.example.prophet_example_spring;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("h2")
class ActionHttpFlowIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void createApproveShipAndQueryOrderOverHttp() {
        String orderId = "order-http-1";

        ResponseEntity<Map> createResponse = restTemplate.postForEntity(
            "/actions/createOrder",
            Map.of(
                "orderId", orderId,
                "customer", Map.of("userId", "user-http-1"),
                "totalAmount", new BigDecimal("42.50"),
                "discountCode", "PROMO10",
                "tags", List.of("vip", "api"),
                "shippingAddress", Map.of(
                    "line1", "123 Test Street",
                    "city", "San Francisco",
                    "countryCode", "US"
                )
            ),
            Map.class
        );
        assertEquals(HttpStatus.OK, createResponse.getStatusCode());
        assertNotNull(createResponse.getBody());
        assertEquals(orderId, createResponse.getBody().get("orderId"));
        assertEquals("created", createResponse.getBody().get("currentState"));

        ResponseEntity<Map> approveResponse = restTemplate.postForEntity(
            "/actions/approveOrder",
            Map.of(
                "orderId", orderId,
                "approvedBy", "approver-1",
                "notes", List.of("looks good"),
                "context", Map.of(
                    "approver", Map.of("userId", "approver-1"),
                    "watchers", List.of(Map.of("userId", "auditor-1")),
                    "reason", "policy-check"
                )
            ),
            Map.class
        );
        assertEquals(HttpStatus.OK, approveResponse.getStatusCode());
        assertNotNull(approveResponse.getBody());
        assertEquals("approved", approveResponse.getBody().get("decision"));

        ResponseEntity<Map> shipResponse = restTemplate.postForEntity(
            "/actions/shipOrder",
            Map.of(
                "orderId", orderId,
                "carrier", "UPS",
                "trackingNumber", "TRACK-001",
                "packageIds", List.of("PKG-1", "PKG-2")
            ),
            Map.class
        );
        assertEquals(HttpStatus.OK, shipResponse.getStatusCode());
        assertNotNull(shipResponse.getBody());
        assertEquals("shipped", shipResponse.getBody().get("shipmentStatus"));
        assertNotNull(shipResponse.getBody().get("labels"));

        ResponseEntity<Map> getOrderResponse = restTemplate.getForEntity("/orders/" + orderId, Map.class);
        assertEquals(HttpStatus.OK, getOrderResponse.getStatusCode());
        assertNotNull(getOrderResponse.getBody());
        assertEquals(orderId, getOrderResponse.getBody().get("orderId"));
        assertEquals("SHIPPED", getOrderResponse.getBody().get("currentState"));

        ResponseEntity<Map> queryResponse = restTemplate.postForEntity(
            "/orders/query",
            Map.of(
                "orderId", Map.of("eq", orderId),
                "currentState", Map.of("eq", "SHIPPED")
            ),
            Map.class
        );
        assertEquals(HttpStatus.OK, queryResponse.getStatusCode());
        assertNotNull(queryResponse.getBody());
        Object itemsRaw = queryResponse.getBody().get("items");
        assertNotNull(itemsRaw);
        List<?> items = (List<?>) itemsRaw;
        assertFalse(items.isEmpty());
    }
}
