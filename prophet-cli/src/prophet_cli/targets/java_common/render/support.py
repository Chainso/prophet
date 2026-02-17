from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from prophet_cli.codegen.rendering import primary_key_fields_for_object
from prophet_cli.codegen.rendering import snake_case

def java_package_segment(value: str) -> str:
    raw = snake_case(value).strip("_")
    if not raw:
        return "ontology"
    normalized = re.sub(r"[^a-z0-9_]", "_", raw)
    if normalized[:1].isdigit():
        return f"o_{normalized}"
    return normalized


def effective_base_package(base_package: str, ontology_name: str) -> str:
    segment = java_package_segment(ontology_name)
    suffix = f".{segment}"
    if base_package.endswith(suffix):
        return base_package
    return f"{base_package}{suffix}"


def java_type_for_type_descriptor(
    t: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    if t["kind"] == "list":
        elem_java = java_type_for_type_descriptor(t["element"], type_by_id, object_by_id, struct_by_id)
        return f"List<{elem_java}>"
    if t["kind"] == "object_ref":
        target = object_by_id[t["target_object_id"]]
        return f"{target['name']}Ref"
    if t["kind"] == "struct":
        target = struct_by_id[t["target_struct_id"]]
        return target["name"]

    if t["kind"] == "base":
        base = t["name"]
    elif t["kind"] == "custom":
        base = type_by_id[t["target_type_id"]]["base"]
    else:
        base = "string"

    return {
        "string": "String",
        "int": "Integer",
        "long": "Long",
        "short": "Short",
        "byte": "Short",
        "double": "Double",
        "float": "Float",
        "decimal": "BigDecimal",
        "boolean": "Boolean",
        "datetime": "OffsetDateTime",
        "date": "LocalDate",
        "duration": "Duration",
    }.get(base, "String")


def java_type_for_field(
    field: Dict[str, Any],
    type_by_id: Dict[str, Dict[str, Any]],
    object_by_id: Dict[str, Dict[str, Any]],
    struct_by_id: Dict[str, Dict[str, Any]],
) -> str:
    return java_type_for_type_descriptor(field["type"], type_by_id, object_by_id, struct_by_id)


def struct_target_ids_for_type(type_desc: Dict[str, Any]) -> List[str]:
    if type_desc.get("kind") == "struct":
        return [type_desc["target_struct_id"]]
    if type_desc.get("kind") == "list":
        return struct_target_ids_for_type(type_desc["element"])
    return []


def add_java_imports_for_type(java_type: str, imports: set[str]) -> None:
    if "List<" in java_type:
        imports.add("import java.util.List;")
    if "BigDecimal" in java_type:
        imports.add("import java.math.BigDecimal;")
    if "OffsetDateTime" in java_type:
        imports.add("import java.time.OffsetDateTime;")
    if "LocalDate" in java_type:
        imports.add("import java.time.LocalDate;")
    if "Duration" in java_type:
        imports.add("import java.time.Duration;")


def _sanitize_javadoc_text(text: str) -> str:
    return text.replace("*/", "*&#47;").strip()


def render_javadoc_block(text: Optional[str], indent: str = "") -> str:
    if text is None:
        return ""
    cleaned = _sanitize_javadoc_text(text)
    if not cleaned:
        return ""
    lines = cleaned.splitlines() or [cleaned]
    rendered = [f"{indent}/**"]
    for line in lines:
        rendered.append(f"{indent} * {line.strip()}")
    rendered.append(f"{indent} */")
    return "\n".join(rendered) + "\n"


def render_java_record_with_builder(
    package_name: str,
    imports: set[str],
    record_name: str,
    fields: List[Tuple[str, str, bool]],
    record_description: Optional[str] = None,
    field_descriptions: Optional[Dict[str, str]] = None,
    implements_types: Optional[List[str]] = None,
) -> str:
    record_components: List[str] = []
    component_docs = field_descriptions or {}
    for java_t, field_name, required in fields:
        ann = "@NotNull " if required else ""
        if required:
            imports.add("import jakarta.validation.constraints.NotNull;")
        field_doc = render_javadoc_block(component_docs.get(field_name), indent="    ")
        component_line = f"    {ann}{java_t} {field_name}"
        if field_doc:
            record_components.append(field_doc + component_line)
        else:
            record_components.append(component_line)

    builder_field_lines = [f"        private {java_t} {field_name};" for java_t, field_name, _ in fields]
    builder_setter_lines: List[str] = []
    for java_t, field_name, _ in fields:
        builder_setter_lines.extend(
            [
                f"        public Builder {field_name}({java_t} value) {{",
                f"            this.{field_name} = value;",
                "            return this;",
                "        }",
                "",
            ]
        )

    builder_build_lines = [
        f"        public {record_name} build() {{",
        f"            return new {record_name}(",
    ]
    for idx, (_, field_name, _) in enumerate(fields):
        suffix = "," if idx < len(fields) - 1 else ""
        builder_build_lines.append(f"                {field_name}{suffix}")
    builder_build_lines.extend(
        [
            "            );",
            "        }",
        ]
    )

    import_block = "\n".join(sorted(imports))
    implements_clause = ""
    if implements_types:
        implements_clause = " implements " + ", ".join(implements_types)
    source = (
        f"package {package_name};\n\n"
        + (f"{import_block}\n\n" if import_block else "")
        + render_javadoc_block(record_description)
        + f"public record {record_name}(\n"
        + ",\n".join(record_components)
        + f"\n){implements_clause} {{\n\n"
        + "    public static Builder builder() {\n"
        + "        return new Builder();\n"
        + "    }\n\n"
        + "    public static final class Builder {\n"
        + ("\n".join(builder_field_lines) + "\n\n" if builder_field_lines else "")
        + "\n".join(builder_setter_lines)
        + "\n".join(builder_build_lines)
        + "\n"
        + "    }\n"
        + "}\n"
    )
    return source


def add_generated_annotation(source: str) -> str:
    if "@Generated(" in source:
        return source

    lines = source.splitlines()
    package_idx = next((i for i, line in enumerate(lines) if line.startswith("package ")), -1)
    if package_idx == -1:
        return source

    generated_import = "import javax.annotation.processing.Generated;"
    if generated_import not in lines:
        first_import = next(
            (i for i, line in enumerate(lines[package_idx + 1 :], start=package_idx + 1) if line.startswith("import ")),
            -1,
        )
        if first_import != -1:
            lines.insert(first_import, generated_import)
        else:
            lines = lines[: package_idx + 1] + ["", generated_import, ""] + lines[package_idx + 1 :]

    type_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if re.match(r"^public\s+(class|interface|record|enum)\s+[A-Za-z_][A-Za-z0-9_]*", line)
        ),
        -1,
    )
    if type_idx == -1:
        return source

    lines.insert(type_idx, '@Generated("prophet-cli")')
    result = "\n".join(lines)
    return result + ("\n" if source.endswith("\n") else "")


def annotate_generated_java_files(files: Dict[str, str]) -> None:
    for rel_path, content in list(files.items()):
        if rel_path.endswith(".java"):
            files[rel_path] = add_generated_annotation(content)


def object_has_composite_primary_key(obj: Dict[str, Any]) -> bool:
    return len(primary_key_fields_for_object(obj)) > 1
