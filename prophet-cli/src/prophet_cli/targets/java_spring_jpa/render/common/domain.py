from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import object_ref_target_ids_for_type
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import render_java_record_with_builder
from prophet_cli.targets.java_common.render.support import struct_target_ids_for_type
from prophet_cli.codegen.rendering import primary_key_field_for_object

def render_domain_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    objects = state["objects"]
    structs = state["structs"]
    action_inputs = state["action_inputs"]
    events = state["events"]
    object_by_id = state["object_by_id"]
    struct_by_id = state["struct_by_id"]
    type_by_id = state["type_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]

    # domain ref records
    ref_types: Dict[str, Dict[str, Any]] = {}
    for source in list(objects) + list(structs) + list(action_inputs):
        for f in source.get("fields", []):
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                ref_types[target["id"]] = target
    for event in events:
        if "object_id" in event:
            target = object_by_id[event["object_id"]]
            ref_types[target["id"]] = target
        for f in event.get("fields", []):
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                ref_types[target["id"]] = target

    for target in sorted(ref_types.values(), key=lambda x: x["id"]):
        ref_or_object_name = f"{target['name']}RefOrObject"
        files[f"src/main/java/{package_path}/generated/domain/{ref_or_object_name}.java"] = (
            f"package {base_package}.generated.domain;\n\n"
            + f"public sealed interface {ref_or_object_name} permits {target['name']}Ref, {target['name']} {{\n"
            + "}\n"
        )

        target_pk = primary_key_field_for_object(target)
        pk_java = java_type_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
        cls = f"{target['name']}Ref"
        ref_fields = [(pk_java, camel_case(target_pk["name"]), True)]
        files[f"src/main/java/{package_path}/generated/domain/{cls}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            set(),
            cls,
            ref_fields,
            record_description=f"Reference to {target['name']} by primary key.",
            field_descriptions={camel_case(target_pk["name"]): f"Primary key for referenced {target['name']}."},
            implements_types=[ref_or_object_name],
        )

    # struct domain records
    for struct in structs:
        imports: set[str] = set()
        struct_fields: List[Tuple[str, str, bool]] = []
        struct_field_descriptions: Dict[str, str] = {}
        for f in struct.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_id in object_ref_target_ids_for_type(f["type"]):
                target = object_by_id[target_id]
                imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                if target_struct["name"] != struct["name"]:
                    imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")
            required = f.get("cardinality", {}).get("min", 0) > 0
            struct_fields.append((java_t, camel_case(f["name"]), required))
            if f.get("description"):
                struct_field_descriptions[camel_case(f["name"])] = str(f["description"])

        files[f"src/main/java/{package_path}/generated/domain/{struct['name']}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            imports,
            struct["name"],
            struct_fields,
            record_description=str(struct.get("description", "")) or None,
            field_descriptions=struct_field_descriptions,
        )

    # state enums + domain records
    for obj in objects:
        if obj.get("states"):
            enum_name = f"{obj['name']}State"
            vals = ",\n    ".join(s["name"].upper() for s in obj["states"])
            files[f"src/main/java/{package_path}/generated/domain/{enum_name}.java"] = (
                f"package {base_package}.generated.domain;\n\n"
                f"public enum {enum_name} {{\n"
                f"    {vals}\n"
                "}\n"
            )

        imports: set[str] = set()
        object_fields: List[Tuple[str, str, bool]] = []
        object_field_descriptions: Dict[str, str] = {}

        for f in obj.get("fields", []):
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

            required = f.get("cardinality", {}).get("min", 0) > 0
            object_fields.append((java_t, camel_case(f["name"]), required))
            if f.get("description"):
                object_field_descriptions[camel_case(f["name"])] = str(f["description"])

        if obj.get("states"):
            object_fields.append((f"{obj['name']}State", "state", True))
            imports.add(f"import {base_package}.generated.domain.{obj['name']}State;")

        files[f"src/main/java/{package_path}/generated/domain/{obj['name']}.java"] = render_java_record_with_builder(
            f"{base_package}.generated.domain",
            imports,
            obj["name"],
            object_fields,
            record_description=str(obj.get("description", "")) or None,
            field_descriptions=object_field_descriptions,
            implements_types=[f"{obj['name']}RefOrObject"] if obj["id"] in ref_types else None,
        )
