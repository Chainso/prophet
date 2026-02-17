package com.example.prophet.commerce_local.generated.events;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.prophet.events.runtime.EventTime;
import io.prophet.events.runtime.EventWireEnvelope;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

public final class EventPublishingSupport {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private EventPublishingSupport() {}

    private record RefBinding(String objectType, List<String> path, List<String> primaryKeys) {}

    private static void applyRefBindings(Map<String, Object> payload, List<RefBinding> bindings, List<Map<String, Object>> updatedObjects) {
        for (RefBinding binding : bindings) {
            applyBindingAtPath(payload, binding, 0, updatedObjects);
        }
    }

    private static void applyBindingAtPath(Object current, RefBinding binding, int pathIndex, List<Map<String, Object>> updatedObjects) {
        if (current == null) {
            return;
        }
        if (pathIndex >= binding.path().size()) {
            return;
        }
        String segment = binding.path().get(pathIndex);
        if ("*".equals(segment)) {
            if (current instanceof List<?> list) {
                for (Object item : list) {
                    applyBindingAtPath(item, binding, pathIndex + 1, updatedObjects);
                }
            }
            return;
        }
        if (!(current instanceof Map<?, ?> rawMap)) {
            return;
        }
        Object nextValue = rawMap.get(segment);
        if (nextValue == null) {
            return;
        }
        if (pathIndex == binding.path().size() - 1) {
            Object normalized = normalizeRefValue(nextValue, binding, updatedObjects);
            @SuppressWarnings("unchecked")
            Map<String, Object> writable = (Map<String, Object>) rawMap;
            writable.put(segment, normalized);
            return;
        }
        applyBindingAtPath(nextValue, binding, pathIndex + 1, updatedObjects);
    }

    private static Object normalizeRefValue(Object value, RefBinding binding, List<Map<String, Object>> updatedObjects) {
        if (!(value instanceof Map<?, ?> rawMap)) {
            return value;
        }
        Map<String, Object> candidate = toStringKeyMap(rawMap);
        if (!containsAllPrimaryKeys(candidate, binding.primaryKeys())) {
            return value;
        }
        if (isRefShape(candidate, binding.primaryKeys())) {
            return candidate;
        }
        Map<String, Object> refValue = new LinkedHashMap<>();
        for (String key : binding.primaryKeys()) {
            refValue.put(key, candidate.get(key));
        }
        Map<String, Object> updated = new LinkedHashMap<>();
        updated.put("object_type", binding.objectType());
        updated.put("object_ref", refValue);
        updated.put("object", candidate);
        updatedObjects.add(updated);
        return refValue;
    }

    private static Map<String, Object> toStringKeyMap(Map<?, ?> rawMap) {
        Map<String, Object> normalized = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : rawMap.entrySet()) {
            normalized.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return normalized;
    }

    private static boolean containsAllPrimaryKeys(Map<String, Object> candidate, List<String> primaryKeys) {
        for (String key : primaryKeys) {
            if (!candidate.containsKey(key) || candidate.get(key) == null) {
                return false;
            }
        }
        return true;
    }

    private static boolean isRefShape(Map<String, Object> candidate, List<String> primaryKeys) {
        for (String key : candidate.keySet()) {
            if (!primaryKeys.contains(key)) {
                return false;
            }
        }
        return true;
    }

    public static EventWireEnvelope toEnvelope(DomainEvent event, String eventId, String traceId, String source, Map<String, String> attributes) {
        String eventType;
        Object payloadValue;
        List<RefBinding> refBindings;
        if (event instanceof ApproveOrderResultEvent typed) {
            eventType = "ApproveOrderResult";
            payloadValue = typed.payload();
            refBindings = List.of(
                new RefBinding("Order", List.of("order"), List.of("orderId"))
            );
        }
        else if (event instanceof CreateOrderResultEvent typed) {
            eventType = "CreateOrderResult";
            payloadValue = typed.payload();
            refBindings = List.of(
                new RefBinding("Order", List.of("order"), List.of("orderId"))
            );
        }
        else if (event instanceof ShipOrderResultEvent typed) {
            eventType = "ShipOrderResult";
            payloadValue = typed.payload();
            refBindings = List.of(
                new RefBinding("Order", List.of("order"), List.of("orderId"))
            );
        }
        else if (event instanceof PaymentCapturedEvent typed) {
            eventType = "PaymentCaptured";
            payloadValue = typed.payload();
            refBindings = List.of(
                new RefBinding("Order", List.of("order"), List.of("orderId"))
            );
        }
        else {
            throw new IllegalArgumentException("Unsupported domain event: " + event.getClass().getName());
        }

        Map<String, Object> payload = MAPPER.convertValue(payloadValue, new TypeReference<Map<String, Object>>() {});
        List<Map<String, Object>> updatedObjects = new ArrayList<>();
        applyRefBindings(payload, refBindings, updatedObjects);
        return new EventWireEnvelope(
            eventId,
            traceId,
            eventType,
            "1.0.0",
            EventTime.nowIso(),
            source,
            payload,
            attributes,
            updatedObjects.isEmpty() ? null : List.copyOf(updatedObjects)
        );
    }

    public static CompletionStage<Void> publishAll(
        io.prophet.events.runtime.EventPublisher eventPublisher,
        List<DomainEvent> events,
        String traceId,
        String source,
        Map<String, String> attributes
    ) {
        if (events == null || events.isEmpty()) {
            return CompletableFuture.completedFuture(null);
        }
        List<EventWireEnvelope> envelopes = events.stream()
            .map(event -> toEnvelope(event, io.prophet.events.runtime.EventIds.createEventId(), traceId, source, attributes))
            .toList();
        return eventPublisher.publishBatch(envelopes);
    }
}
