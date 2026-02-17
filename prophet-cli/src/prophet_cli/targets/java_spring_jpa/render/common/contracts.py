from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import object_ref_target_ids_for_type
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.codegen.rendering import primary_key_field_for_object
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import java_type_for_type_descriptor
from prophet_cli.targets.java_common.render.support import render_java_record_with_builder
from prophet_cli.targets.java_common.render.support import struct_target_ids_for_type


def _java_event_type_for_descriptor(
    type_desc: Dict[str, Any],
    *,
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    kind = str(type_desc.get("kind", ""))
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        element_java = _java_event_type_for_descriptor(
            element,
            type_by_id=type_by_id,
            object_by_id=object_by_id,
            struct_by_id=struct_by_id,
        )
        return f"List<{element_java}>"
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        target = object_by_id.get(object_id)
        if isinstance(target, dict):
            return f"{target['name']}RefOrObject"
        return "Object"
    return java_type_for_type_descriptor(type_desc, type_by_id, object_by_id, struct_by_id)


def _collect_event_ref_specs_for_type(
    type_desc: Dict[str, Any],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
    path: List[str],
) -> List[Dict[str, Any]]:
    kind = str(type_desc.get("kind", ""))
    if kind == "object_ref":
        object_id = str(type_desc.get("target_object_id", ""))
        target = object_by_id.get(object_id)
        if not isinstance(target, dict):
            return []
        pk_field = primary_key_field_for_object(target)
        return [
            {
                "object_name": str(target.get("name", "Object")),
                "primary_keys": [camel_case(str(pk_field.get("name", "id")))],
                "path": list(path),
            }
        ]
    if kind == "list":
        element = type_desc.get("element", {}) if isinstance(type_desc.get("element"), dict) else {}
        return _collect_event_ref_specs_for_type(
            element,
            object_by_id=object_by_id,
            struct_by_id=struct_by_id,
            path=path + ["*"],
        )
    if kind == "struct":
        struct_id = str(type_desc.get("target_struct_id", ""))
        struct = struct_by_id.get(struct_id)
        if not isinstance(struct, dict):
            return []
        specs: List[Dict[str, Any]] = []
        for field in list(struct.get("fields", [])):
            if not isinstance(field, dict):
                continue
            field_type = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
            specs.extend(
                _collect_event_ref_specs_for_type(
                    field_type,
                    object_by_id=object_by_id,
                    struct_by_id=struct_by_id,
                    path=path + [camel_case(str(field.get("name", "field")))],
                )
            )
        return specs
    return []


def _collect_event_ref_specs_for_fields(
    fields: List[Dict[str, Any]],
    *,
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_type = field.get("type", {}) if isinstance(field.get("type"), dict) else {}
        specs.extend(
            _collect_event_ref_specs_for_type(
                field_type,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
                path=[camel_case(str(field.get("name", "field")))],
            )
        )
    return _dedupe_event_ref_specs(specs)


def _dedupe_event_ref_specs(specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: Dict[Tuple[str, Tuple[str, ...], Tuple[str, ...]], Dict[str, Any]] = {}
    for spec in specs:
        key = (
            str(spec.get("object_name", "")),
            tuple(str(item) for item in spec.get("primary_keys", [])),
            tuple(str(item) for item in spec.get("path", [])),
        )
        unique[key] = {
            "object_name": key[0],
            "primary_keys": list(key[1]),
            "path": list(key[2]),
        }
    return [unique[key] for key in sorted(unique.keys())]


def _java_string_list_literal(values: List[str]) -> str:
    if not values:
        return "List.of()"
    encoded = ", ".join(f'"{value}"' for value in values)
    return f"List.of({encoded})"


def render_contract_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    action_inputs = state["action_inputs"]
    events = state["events"]
    object_by_id = state["object_by_id"]
    struct_by_id = state["struct_by_id"]
    type_by_id = state["type_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]
    schema_version = str(state.get("ontology_version", "1.0.0"))

    # action contract records
    action_shapes = sorted(action_inputs, key=lambda x: x["id"])
    for shape in action_shapes:
        imports: set[str] = set()
        shape_fields: List[Tuple[str, str, bool]] = []
        shape_field_descriptions: Dict[str, str] = {}
        for f in shape.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
            required = f.get("cardinality", {}).get("min", 0) > 0
            shape_fields.append((java_t, camel_case(f["name"]), required))
            if f.get("description"):
                shape_field_descriptions[camel_case(f["name"])] = str(f["description"])

        record_src = render_java_record_with_builder(
            f"{base_package}.generated.actions",
            imports,
            shape["name"],
            shape_fields,
            record_description=str(shape.get("description", "")) or None,
            field_descriptions=shape_field_descriptions,
        )
        files[f"src/main/java/{package_path}/generated/actions/{shape['name']}.java"] = record_src

    # event payload contracts and domain event wrappers
    domain_event_specs: List[Dict[str, Any]] = []

    for event in sorted(events, key=lambda x: x["id"]):
        event_name = str(event["name"])

        event_fields: List[Tuple[str, str, bool]] = []
        event_imports: set[str] = set()
        event_field_descriptions: Dict[str, str] = {}
        event_payload_fields = [field for field in event.get("fields", []) if isinstance(field, dict)]
        event_ref_specs = _collect_event_ref_specs_for_fields(
            event_payload_fields,
            object_by_id=object_by_id,
            struct_by_id=struct_by_id,
        )
        for f in event_payload_fields:
            java_t = _java_event_type_for_descriptor(
                f["type"],
                type_by_id=type_by_id,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
            add_java_imports_for_type(java_t, event_imports)
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                event_imports.add(f"import {base_package}.generated.domain.{target['name']}RefOrObject;")
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                event_imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
            required = f.get("cardinality", {}).get("min", 0) > 0
            event_fields.append((java_t, camel_case(f["name"]), required))
            if f.get("description"):
                event_field_descriptions[camel_case(f["name"])] = str(f["description"])

        event_record_src = render_java_record_with_builder(
            f"{base_package}.generated.events",
            event_imports,
            event_name,
            event_fields,
            record_description=str(event.get("description", "")).strip() or f"Event payload for '{event_name}'.",
            field_descriptions=event_field_descriptions,
        )
        files[f"src/main/java/{package_path}/generated/events/{event_name}.java"] = event_record_src

        domain_event_specs.append(
            {
                "event_name": event_name,
                "payload_type": event_name,
                "ref_specs": event_ref_specs,
            }
        )

    if domain_event_specs:
        permits = ", ".join([f"{spec['event_name']}Event" for spec in domain_event_specs])
        domain_event_interface = (
            f"package {base_package}.generated.events;\n\n"
            + "public sealed interface DomainEvent permits "
            + permits
            + " {\n"
            + "}\n"
        )
    else:
        domain_event_interface = (
            f"package {base_package}.generated.events;\n\n"
            + "public interface DomainEvent {\n"
            + "}\n"
        )
    files[f"src/main/java/{package_path}/generated/events/DomainEvent.java"] = domain_event_interface

    for spec in domain_event_specs:
        event_name = str(spec["event_name"])
        payload_type = str(spec["payload_type"])
        wrapper_src = (
            f"package {base_package}.generated.events;\n\n"
            + f"public record {event_name}Event({payload_type} payload) implements DomainEvent {{\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/events/{event_name}Event.java"] = wrapper_src

    action_outcome_src = (
        f"package {base_package}.generated.events;\n\n"
        + "import java.util.List;\n\n"
        + "public record ActionOutcome<T>(T output, List<DomainEvent> additionalEvents) {\n"
        + "    public ActionOutcome {\n"
        + "        additionalEvents = additionalEvents == null ? List.of() : List.copyOf(additionalEvents);\n"
        + "    }\n"
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/events/ActionOutcome.java"] = action_outcome_src

    action_outcomes_src = (
        f"package {base_package}.generated.events;\n\n"
        + "import java.util.Arrays;\n"
        + "import java.util.List;\n\n"
        + "public final class ActionOutcomes {\n"
        + "    private ActionOutcomes() {}\n\n"
        + "    public static <T> ActionOutcome<T> just(T output) {\n"
        + "        return new ActionOutcome<>(output, List.of());\n"
        + "    }\n\n"
        + "    public static <T> ActionOutcome<T> withEvents(T output, DomainEvent... additionalEvents) {\n"
        + "        return new ActionOutcome<>(output, Arrays.asList(additionalEvents));\n"
        + "    }\n"
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/events/ActionOutcomes.java"] = action_outcomes_src

    mapper_lines: List[str] = [
        f"package {base_package}.generated.events;",
        "",
        "import com.fasterxml.jackson.core.type.TypeReference;",
        "import com.fasterxml.jackson.databind.ObjectMapper;",
        "import io.prophet.events.runtime.EventTime;",
        "import io.prophet.events.runtime.EventWireEnvelope;",
        "import java.util.ArrayList;",
        "import java.util.LinkedHashMap;",
        "import java.util.List;",
        "import java.util.Map;",
        "import java.util.concurrent.CompletableFuture;",
        "import java.util.concurrent.CompletionStage;",
        "",
        "public final class EventPublishingSupport {",
        "    private static final ObjectMapper MAPPER = new ObjectMapper();",
        "",
        "    private EventPublishingSupport() {}",
        "",
        "    private record RefBinding(String objectType, List<String> path, List<String> primaryKeys) {}",
        "",
        "    private static void applyRefBindings(Map<String, Object> payload, List<RefBinding> bindings, List<Map<String, Object>> updatedObjects) {",
        "        for (RefBinding binding : bindings) {",
        "            applyBindingAtPath(payload, binding, 0, updatedObjects);",
        "        }",
        "    }",
        "",
        "    private static void applyBindingAtPath(Object current, RefBinding binding, int pathIndex, List<Map<String, Object>> updatedObjects) {",
        "        if (current == null) {",
        "            return;",
        "        }",
        "        if (pathIndex >= binding.path().size()) {",
        "            return;",
        "        }",
        "        String segment = binding.path().get(pathIndex);",
        "        if (\"*\".equals(segment)) {",
        "            if (current instanceof List<?> list) {",
        "                for (Object item : list) {",
        "                    applyBindingAtPath(item, binding, pathIndex + 1, updatedObjects);",
        "                }",
        "            }",
        "            return;",
        "        }",
        "        if (!(current instanceof Map<?, ?> rawMap)) {",
        "            return;",
        "        }",
        "        Object nextValue = rawMap.get(segment);",
        "        if (nextValue == null) {",
        "            return;",
        "        }",
        "        if (pathIndex == binding.path().size() - 1) {",
        "            Object normalized = normalizeRefValue(nextValue, binding, updatedObjects);",
        "            @SuppressWarnings(\"unchecked\")",
        "            Map<String, Object> writable = (Map<String, Object>) rawMap;",
        "            writable.put(segment, normalized);",
        "            return;",
        "        }",
        "        applyBindingAtPath(nextValue, binding, pathIndex + 1, updatedObjects);",
        "    }",
        "",
        "    private static Object normalizeRefValue(Object value, RefBinding binding, List<Map<String, Object>> updatedObjects) {",
        "        if (!(value instanceof Map<?, ?> rawMap)) {",
        "            return value;",
        "        }",
        "        Map<String, Object> candidate = toStringKeyMap(rawMap);",
        "        if (!containsAllPrimaryKeys(candidate, binding.primaryKeys())) {",
        "            return value;",
        "        }",
        "        if (isRefShape(candidate, binding.primaryKeys())) {",
        "            return candidate;",
        "        }",
        "        Map<String, Object> refValue = new LinkedHashMap<>();",
        "        for (String key : binding.primaryKeys()) {",
        "            refValue.put(key, candidate.get(key));",
        "        }",
        "        Map<String, Object> updated = new LinkedHashMap<>();",
        "        updated.put(\"object_type\", binding.objectType());",
        "        updated.put(\"object_ref\", refValue);",
        "        updated.put(\"object\", candidate);",
        "        updatedObjects.add(updated);",
        "        return refValue;",
        "    }",
        "",
        "    private static Map<String, Object> toStringKeyMap(Map<?, ?> rawMap) {",
        "        Map<String, Object> normalized = new LinkedHashMap<>();",
        "        for (Map.Entry<?, ?> entry : rawMap.entrySet()) {",
        "            normalized.put(String.valueOf(entry.getKey()), entry.getValue());",
        "        }",
        "        return normalized;",
        "    }",
        "",
        "    private static boolean containsAllPrimaryKeys(Map<String, Object> candidate, List<String> primaryKeys) {",
        "        for (String key : primaryKeys) {",
        "            if (!candidate.containsKey(key) || candidate.get(key) == null) {",
        "                return false;",
        "            }",
        "        }",
        "        return true;",
        "    }",
        "",
        "    private static boolean isRefShape(Map<String, Object> candidate, List<String> primaryKeys) {",
        "        for (String key : candidate.keySet()) {",
        "            if (!primaryKeys.contains(key)) {",
        "                return false;",
        "            }",
        "        }",
        "        return true;",
        "    }",
        "",
        "    public static EventWireEnvelope toEnvelope(DomainEvent event, String eventId, String traceId, String source, Map<String, String> attributes) {",
        "        String eventType;",
        "        Object payloadValue;",
        "        List<RefBinding> refBindings;",
    ]

    for idx, spec in enumerate(domain_event_specs):
        event_name = str(spec["event_name"])
        wrapper_name = f"{event_name}Event"
        ref_specs = [item for item in spec.get("ref_specs", []) if isinstance(item, dict)]
        keyword = "if" if idx == 0 else "else if"
        mapper_lines.extend(
            [
                f"        {keyword} (event instanceof {wrapper_name} typed) {{",
                f"            eventType = \"{event_name}\";",
                "            payloadValue = typed.payload();",
            ]
        )
        if ref_specs:
            mapper_lines.append("            refBindings = List.of(")
            for spec_idx, ref_spec in enumerate(ref_specs):
                object_name = str(ref_spec.get("object_name", "Object"))
                path_literal = _java_string_list_literal([str(item) for item in ref_spec.get("path", [])])
                key_literal = _java_string_list_literal([str(item) for item in ref_spec.get("primary_keys", [])])
                suffix = "," if spec_idx < len(ref_specs) - 1 else ""
                mapper_lines.append(
                    f"                new RefBinding(\"{object_name}\", {path_literal}, {key_literal}){suffix}"
                )
            mapper_lines.append("            );")
        else:
            mapper_lines.append("            refBindings = List.of();")
        mapper_lines.append("        }")

    mapper_lines.extend(
        [
            "        else {",
            "            throw new IllegalArgumentException(\"Unsupported domain event: \" + event.getClass().getName());",
            "        }",
            "",
            "        Map<String, Object> payload = MAPPER.convertValue(payloadValue, new TypeReference<Map<String, Object>>() {});",
            "        List<Map<String, Object>> updatedObjects = new ArrayList<>();",
            "        applyRefBindings(payload, refBindings, updatedObjects);",
            "        return new EventWireEnvelope(",
            "            eventId,",
            "            traceId,",
            "            eventType,",
            f"            \"{schema_version}\",",
            "            EventTime.nowIso(),",
            "            source,",
            "            payload,",
            "            attributes,",
            "            updatedObjects.isEmpty() ? null : List.copyOf(updatedObjects)",
            "        );",
            "    }",
            "",
            "    public static CompletionStage<Void> publishAll(",
            "        io.prophet.events.runtime.EventPublisher eventPublisher,",
            "        List<DomainEvent> events,",
            "        String traceId,",
            "        String source,",
            "        Map<String, String> attributes",
            "    ) {",
            "        if (events == null || events.isEmpty()) {",
            "            return CompletableFuture.completedFuture(null);",
            "        }",
            "        List<EventWireEnvelope> envelopes = events.stream()",
            "            .map(event -> toEnvelope(event, io.prophet.events.runtime.EventIds.createEventId(), traceId, source, attributes))",
            "            .toList();",
            "        return eventPublisher.publishBatch(envelopes);",
            "    }",
            "}",
            "",
        ]
    )
    files[f"src/main/java/{package_path}/generated/events/EventPublishingSupport.java"] = "\n".join(mapper_lines)

    no_op_src = (
        f"package {base_package}.generated.events;\n\n"
        + "import io.prophet.events.runtime.EventPublisher;\n"
        + "import io.prophet.events.runtime.EventWireEnvelope;\n"
        + "import java.util.List;\n"
        + "import java.util.concurrent.CompletableFuture;\n"
        + "import java.util.concurrent.CompletionStage;\n"
        + "import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;\n"
        + "import org.springframework.stereotype.Component;\n\n"
        + "@Component\n"
        + "@ConditionalOnMissingBean(value = EventPublisher.class, ignored = EventPublisherNoOp.class)\n"
        + "public class EventPublisherNoOp implements EventPublisher {\n"
        + "    @Override\n"
        + "    public CompletionStage<Void> publish(EventWireEnvelope envelope) {\n"
        + "        return CompletableFuture.completedFuture(null);\n"
        + "    }\n\n"
        + "    @Override\n"
        + "    public CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes) {\n"
        + "        return CompletableFuture.completedFuture(null);\n"
        + "    }\n"
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/events/EventPublisherNoOp.java"] = no_op_src
