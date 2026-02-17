from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..support import _camel_case
from ..support import _object_primary_key_fields
from ..support import _pascal_case


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
        pk_fields = _object_primary_key_fields(target)
        if not pk_fields:
            return []
        return [
            {
                "object_name": _pascal_case(str(target.get("name", "Object"))),
                "path": list(path),
                "primary_keys": [_camel_case(str(field.get("name", "id"))) for field in pk_fields],
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
                    path=path + [_camel_case(str(field.get("name", "field")))],
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
                path=[_camel_case(str(field.get("name", "field")))],
            )
        )
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


def _js_string_list(values: List[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join([f"'{value}'" for value in values]) + "]"


def _render_event_emitter(ir: Dict[str, Any]) -> str:
    output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}
    object_by_id = {item["id"]: item for item in ir.get("objects", []) if isinstance(item, dict) and "id" in item}
    struct_by_id = {item["id"]: item for item in ir.get("structs", []) if isinstance(item, dict) and "id" in item}
    schema_version = str(ir.get("ontology", {}).get("version", "1.0.0"))

    domain_variants: List[str] = []
    constructor_lines: List[str] = []
    switch_lines: List[str] = []
    unique_events: List[Dict[str, Any]] = []
    seen_event_names: set[str] = set()

    for event in sorted(ir.get("events", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind", ""))
        if kind not in {"action_output", "signal"}:
            continue
        event_name = _pascal_case(str(event.get("name", "Event")))
        if event_name in seen_event_names:
            continue
        seen_event_names.add(event_name)
        if kind == "action_output":
            shape_id = str(event.get("output_shape_id", ""))
            output_shape = output_by_id.get(shape_id, {})
            payload_type = f"Actions.{_pascal_case(str(output_shape.get('name', event_name)))}"
            fields = [field for field in output_shape.get("fields", []) if isinstance(field, dict)]
            ref_specs = _collect_event_ref_specs_for_fields(
                fields,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
        else:
            payload_type = f"EventContracts.{event_name}"
            fields = [field for field in event.get("fields", []) if isinstance(field, dict)]
            ref_specs = _collect_event_ref_specs_for_fields(
                fields,
                object_by_id=object_by_id,
                struct_by_id=struct_by_id,
            )
        unique_events.append({"event_name": event_name, "payload_type": payload_type, "ref_specs": ref_specs})

    for item in unique_events:
        event_name = str(item["event_name"])
        payload_type = str(item["payload_type"])
        ref_specs = [spec for spec in item.get("ref_specs", []) if isinstance(spec, dict)]
        domain_variants.append(f"  | {{ type: '{event_name}'; payload: {payload_type} }}")
        constructor_name = f"create{event_name}Event"
        constructor_lines.extend(
            [
                f"export function {constructor_name}(payload: {payload_type}): DomainEvent {{",
                f"  return {{ type: '{event_name}', payload }};",
                "}",
                "",
            ]
        )

        if ref_specs:
            binding_lines = [
                "[",
            ]
            for spec in ref_specs:
                binding_lines.append(
                    "          { "
                    + f"objectType: '{str(spec.get('object_name', 'Object'))}', "
                    + f"path: {_js_string_list([str(value) for value in spec.get('path', [])])}, "
                    + f"primaryKeys: {_js_string_list([str(value) for value in spec.get('primary_keys', [])])}"
                    + " },"
                )
            binding_lines.append("        ]")
            bindings_expr = "\n".join(binding_lines)
        else:
            bindings_expr = "[]"

        switch_lines.extend(
            [
                f"    case '{event_name}': {{",
                "      const payload = cloneJsonLike(event.payload) as Record<string, unknown>;",
                f"      const updatedObjects = normalizePayloadRefs(payload, {bindings_expr});",
                "      return {",
                "        event_id: createEventId(),",
                "        trace_id: metadata.traceId,",
                f"        event_type: '{event_name}',",
                f"        schema_version: '{schema_version}',",
                "        occurred_at: nowIso(),",
                "        source: metadata.source,",
                "        payload,",
                "        attributes: metadata.attributes,",
                "        updated_objects: updatedObjects.length ? updatedObjects : undefined,",
                "      };",
                "    }",
            ]
        )

    lines: List[str] = [
        "// Code generated by prophet-cli. DO NOT EDIT.",
        "",
        "import type * as Actions from './actions';",
        "import type * as EventContracts from './event-contracts';",
        "import { createEventId, nowIso, NoOpEventPublisher, type EventPublisher, type EventUpdatedObject, type EventWireEnvelope } from '@prophet-ontology/events-runtime';",
        "",
    ]

    if domain_variants:
        lines.append("export type DomainEvent =")
        lines.extend(domain_variants)
        lines.append("")
    else:
        lines.append("export type DomainEvent = never;")
        lines.append("")

    lines.extend(
        [
            "interface RefPathBinding {",
            "  objectType: string;",
            "  path: string[];",
            "  primaryKeys: string[];",
            "}",
            "",
            "function isRecord(value: unknown): value is Record<string, unknown> {",
            "  return value !== null && typeof value === 'object' && !Array.isArray(value);",
            "}",
            "",
            "function cloneJsonLike(value: unknown): unknown {",
            "  if (Array.isArray(value)) {",
            "    return value.map((item) => cloneJsonLike(item));",
            "  }",
            "  if (isRecord(value)) {",
            "    const copy: Record<string, unknown> = {};",
            "    for (const [key, item] of Object.entries(value)) {",
            "      copy[key] = cloneJsonLike(item);",
            "    }",
            "    return copy;",
            "  }",
            "  return value;",
            "}",
            "",
            "function containsAllPrimaryKeys(candidate: Record<string, unknown>, primaryKeys: string[]): boolean {",
            "  return primaryKeys.every((key) => Object.prototype.hasOwnProperty.call(candidate, key) && candidate[key] != null);",
            "}",
            "",
            "function isRefShape(candidate: Record<string, unknown>, primaryKeys: string[]): boolean {",
            "  return Object.keys(candidate).every((key) => primaryKeys.includes(key));",
            "}",
            "",
            "function normalizeRefValue(value: unknown, binding: RefPathBinding, updatedObjects: EventUpdatedObject[]): unknown {",
            "  if (!isRecord(value)) {",
            "    return value;",
            "  }",
            "  if (!containsAllPrimaryKeys(value, binding.primaryKeys)) {",
            "    return value;",
            "  }",
            "  if (isRefShape(value, binding.primaryKeys)) {",
            "    return value;",
            "  }",
            "  const objectRef: Record<string, unknown> = {};",
            "  for (const key of binding.primaryKeys) {",
            "    objectRef[key] = value[key];",
            "  }",
            "  updatedObjects.push({",
            "    object_type: binding.objectType,",
            "    object_ref: objectRef,",
            "    object: value,",
            "  });",
            "  return objectRef;",
            "}",
            "",
            "function applyBindingAtPath(current: unknown, binding: RefPathBinding, pathIndex: number, updatedObjects: EventUpdatedObject[]): void {",
            "  if (pathIndex >= binding.path.length) {",
            "    return;",
            "  }",
            "  const segment = binding.path[pathIndex];",
            "  if (segment === '*') {",
            "    if (Array.isArray(current)) {",
            "      for (const item of current) {",
            "        applyBindingAtPath(item, binding, pathIndex + 1, updatedObjects);",
            "      }",
            "    }",
            "    return;",
            "  }",
            "  if (!isRecord(current)) {",
            "    return;",
            "  }",
            "  const nextValue = current[segment];",
            "  if (nextValue == null) {",
            "    return;",
            "  }",
            "  if (pathIndex === binding.path.length - 1) {",
            "    current[segment] = normalizeRefValue(nextValue, binding, updatedObjects);",
            "    return;",
            "  }",
            "  applyBindingAtPath(nextValue, binding, pathIndex + 1, updatedObjects);",
            "}",
            "",
            "function normalizePayloadRefs(payload: Record<string, unknown>, bindings: RefPathBinding[]): EventUpdatedObject[] {",
            "  const updatedObjects: EventUpdatedObject[] = [];",
            "  for (const binding of bindings) {",
            "    applyBindingAtPath(payload, binding, 0, updatedObjects);",
            "  }",
            "  return updatedObjects;",
            "}",
            "",
            "export interface ActionOutcome<TOutput> {",
            "  output: TOutput;",
            "  additionalEvents: DomainEvent[];",
            "}",
            "",
            "export type ActionOutcomeValue<TOutput> = TOutput | ActionOutcome<TOutput>;",
            "",
            "export interface EventPublishMetadata {",
            "  traceId: string;",
            "  source: string;",
            "  attributes?: Record<string, string>;",
            "}",
            "",
            "export function just<TOutput>(output: TOutput): ActionOutcome<TOutput> {",
            "  return { output, additionalEvents: [] };",
            "}",
            "",
            "export function withEvents<TOutput>(output: TOutput, ...additionalEvents: DomainEvent[]): ActionOutcome<TOutput> {",
            "  return { output, additionalEvents };",
            "}",
            "",
            "export function toActionOutcome<TOutput>(value: ActionOutcomeValue<TOutput>): ActionOutcome<TOutput> {",
            "  if (value && typeof value === 'object' && 'output' in value && 'additionalEvents' in value) {",
            "    return value as ActionOutcome<TOutput>;",
            "  }",
            "  return just(value as TOutput);",
            "}",
            "",
        ]
    )

    lines.extend(constructor_lines)

    lines.extend(
        [
            "function toEventWireEnvelope(event: DomainEvent, metadata: EventPublishMetadata): EventWireEnvelope {",
            "  switch (event.type) {",
        ]
    )
    lines.extend(switch_lines)
    lines.extend(
        [
            "    default:",
            "      throw new Error(`Unsupported domain event: ${(event as { type?: string }).type ?? 'unknown'}`);",
            "  }",
            "}",
            "",
            "export async function publishDomainEvents(",
            "  eventPublisher: EventPublisher,",
            "  events: DomainEvent[],",
            "  metadata: EventPublishMetadata,",
            "): Promise<void> {",
            "  if (!events.length) {",
            "    return;",
            "  }",
            "  const envelopes = events.map((event) => toEventWireEnvelope(event, metadata));",
            "  await eventPublisher.publishBatch(envelopes);",
            "}",
            "",
            "export { EventPublisher, EventWireEnvelope, NoOpEventPublisher };",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"
