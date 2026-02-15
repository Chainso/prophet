from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import object_ref_target_ids_for_type
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import render_javadoc_block
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

    # event contract records and emitter contract
    emitter_specs: List[Tuple[str, str, str, str]] = []
    emitter_imports: set[str] = set()
    for event in sorted(events, key=lambda x: x["id"]):
        event_kind = str(event.get("kind", "signal"))
        event_name = str(event["name"])
        method_name = f"emit{pascal_case(event_name)}"
        method_description = str(event.get("description", "")).strip() or f"Emit '{event_name}'."

        if event_kind == "action_output":
            output_shape = action_output_by_id.get(str(event.get("output_shape_id", "")))
            if output_shape is None:
                continue
            param_type = str(output_shape["name"])
            emitter_imports.add(f"import {base_package}.generated.actions.{param_type};")
            emitter_specs.append((event_name, method_name, param_type, method_description))
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
            record_description=method_description or None,
            field_descriptions=event_field_descriptions,
        )
        files[f"src/main/java/{package_path}/generated/events/{event_name}.java"] = event_record_src
        emitter_imports.add(f"import {base_package}.generated.events.{event_name};")
        emitter_specs.append((event_name, method_name, event_name, method_description))

    emitter_methods: List[str] = []
    for _, method_name, param_type, method_description in emitter_specs:
        method_doc = render_javadoc_block(method_description, indent="    ").rstrip("\n")
        if method_doc:
            emitter_methods.append(method_doc)
        emitter_methods.append(f"    void {method_name}({param_type} event);")
        emitter_methods.append("")
    emitter_src = (
        f"package {base_package}.generated.events;\n\n"
        + ("".join(f"{line}\n" for line in sorted(emitter_imports)) + "\n" if emitter_imports else "")
        + "public interface GeneratedEventEmitter {\n"
        + ("".join(f"{line}\n" for line in emitter_methods) if emitter_methods else "")
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/events/GeneratedEventEmitter.java"] = emitter_src

    no_op_imports = {
        "import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;",
        "import org.springframework.stereotype.Component;",
    }
    no_op_imports.update(emitter_imports)
    no_op_methods: List[str] = []
    for _, method_name, param_type, _ in emitter_specs:
        no_op_methods.extend(
            [
                "    @Override",
                f"    public void {method_name}({param_type} event) {{",
                "    }",
                "",
            ]
        )
    no_op_src = (
        f"package {base_package}.generated.events;\n\n"
        + "\n".join(sorted(no_op_imports))
        + "\n\n"
        + "@Component\n"
        + "@ConditionalOnMissingBean(value = GeneratedEventEmitter.class, ignored = GeneratedEventEmitterNoOp.class)\n"
        + "public class GeneratedEventEmitterNoOp implements GeneratedEventEmitter {\n"
        + "".join(f"{line}\n" for line in no_op_methods)
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/events/GeneratedEventEmitterNoOp.java"] = no_op_src
