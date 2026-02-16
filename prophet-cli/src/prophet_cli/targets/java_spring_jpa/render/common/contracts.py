from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import object_ref_target_ids_for_type
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import render_java_record_with_builder
from prophet_cli.targets.java_common.render.support import struct_target_ids_for_type


def render_contract_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    action_inputs = state["action_inputs"]
    action_outputs = state["action_outputs"]
    action_output_by_id = state["action_output_by_id"]
    events = state["events"]
    object_by_id = state["object_by_id"]
    struct_by_id = state["struct_by_id"]
    type_by_id = state["type_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]
    schema_version = str(state.get("ontology_version", "1.0.0"))
    action_output_names = {str(item.get("name", "")) for item in action_outputs if isinstance(item, dict)}

    # action contract records
    action_shapes = sorted(action_inputs + action_outputs, key=lambda x: x["id"])
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
    domain_event_specs: List[Tuple[str, str]] = []
    domain_event_imports: set[str] = set()

    for event in sorted(events, key=lambda x: x["id"]):
        event_kind = str(event.get("kind", "signal"))
        event_name = str(event["name"])

        if event_kind == "action_output":
            output_shape = action_output_by_id.get(str(event.get("output_shape_id", "")))
            if output_shape is None:
                continue
            payload_type = str(output_shape["name"])
            domain_event_imports.add(f"import {base_package}.generated.actions.{payload_type};")
            domain_event_specs.append((event_name, payload_type))
            continue

        event_fields: List[Tuple[str, str, bool]] = []
        event_imports: set[str] = set()
        event_field_descriptions: Dict[str, str] = {}

        if event_kind == "signal":
            for f in event.get("fields", []):
                java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
                add_java_imports_for_type(java_t, event_imports)
                for target_id in object_ref_target_ids_for_type(f["type"]):
                    target = object_by_id[target_id]
                    event_imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
                for target_struct_id in struct_target_ids_for_type(f["type"]):
                    target_struct = struct_by_id[target_struct_id]
                    event_imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
                required = f.get("cardinality", {}).get("min", 0) > 0
                event_fields.append((java_t, camel_case(f["name"]), required))
                if f.get("description"):
                    event_field_descriptions[camel_case(f["name"])] = str(f["description"])
        elif event_kind == "transition":
            object_id = event.get("object_id")
            if object_id in object_by_id:
                object_model = object_by_id[object_id]
                object_ref_name = f"{object_model['name']}Ref"
                event_imports.add(f"import {base_package}.generated.domain.{object_ref_name};")
                event_fields.append((object_ref_name, "objectRef", False))
                event_field_descriptions["objectRef"] = (
                    f"Reference to the {object_model['name']} instance associated with this transition."
                )

        event_record_src = render_java_record_with_builder(
            f"{base_package}.generated.events",
            event_imports,
            event_name,
            event_fields,
            record_description=str(event.get("description", "")).strip() or f"Event payload for '{event_name}'.",
            field_descriptions=event_field_descriptions,
        )
        files[f"src/main/java/{package_path}/generated/events/{event_name}.java"] = event_record_src

        if event_kind == "signal":
            domain_event_imports.add(f"import {base_package}.generated.events.{event_name};")
            domain_event_specs.append((event_name, event_name))

    if domain_event_specs:
        permits = ", ".join([f"{name}Event" for name, _ in domain_event_specs])
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

    for event_name, payload_type in domain_event_specs:
        wrapper_imports = ""
        if payload_type in action_output_names:
            wrapper_imports = f"import {base_package}.generated.actions.{payload_type};\n\n"
        wrapper_src = (
            f"package {base_package}.generated.events;\n\n"
            + wrapper_imports
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
        "    public static EventWireEnvelope toEnvelope(DomainEvent event, String eventId, String traceId, String source, Map<String, String> attributes) {",
        "        String eventType;",
        "        Object payloadValue;",
    ]

    for idx, (event_name, _) in enumerate(domain_event_specs):
        wrapper_name = f"{event_name}Event"
        keyword = "if" if idx == 0 else "else if"
        mapper_lines.extend(
            [
                f"        {keyword} (event instanceof {wrapper_name} typed) {{",
                f"            eventType = \"{event_name}\";",
                "            payloadValue = typed.payload();",
                "        }",
            ]
        )
    mapper_lines.extend(
        [
            "        else {",
            "            throw new IllegalArgumentException(\"Unsupported domain event: \" + event.getClass().getName());",
            "        }",
            "",
            "        Map<String, Object> payload = MAPPER.convertValue(payloadValue, new TypeReference<Map<String, Object>>() {});",
            "        return new EventWireEnvelope(",
            "            eventId,",
            "            traceId,",
            "            eventType,",
            f"            \"{schema_version}\",",
            "            EventTime.nowIso(),",
            "            source,",
            "            payload,",
            "            attributes",
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
