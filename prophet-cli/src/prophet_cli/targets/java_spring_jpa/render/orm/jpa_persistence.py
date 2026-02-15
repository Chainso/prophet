from __future__ import annotations

from typing import Any, Dict, List, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import object_ref_target_ids_for_type
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.codegen.rendering import pluralize
from prophet_cli.codegen.rendering import primary_key_field_for_object
from prophet_cli.codegen.rendering import primary_key_fields_for_object
from prophet_cli.codegen.rendering import snake_case
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import java_type_for_type_descriptor
from prophet_cli.targets.java_common.render.support import object_has_composite_primary_key
from prophet_cli.targets.java_common.render.support import render_javadoc_block
from prophet_cli.targets.java_common.render.support import render_java_record_with_builder
from prophet_cli.targets.java_common.render.support import struct_target_ids_for_type

def render_jpa_persistence_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    objects = state["objects"]
    type_by_id = state["type_by_id"]
    object_by_id = state["object_by_id"]
    struct_by_id = state["struct_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]

    # persistence entities and repositories
    for obj in objects:
        fields = obj.get("fields", [])
        pk_fields = primary_key_fields_for_object(obj)
        pk = pk_fields[0]
        composite_pk = len(pk_fields) > 1
        entity_name = f"{obj['name']}Entity"
        table_name = pluralize(snake_case(obj["name"]))

        imports = {
            "import jakarta.persistence.Column;",
            "import jakarta.persistence.Convert;",
            "import jakarta.persistence.Entity;",
            "import jakarta.persistence.Id;",
            "import jakarta.persistence.PrePersist;",
            "import jakarta.persistence.PreUpdate;",
            "import jakarta.persistence.Table;",
            "import jakarta.persistence.Version;",
            "import java.time.OffsetDateTime;",
        }
        if composite_pk:
            imports.add("import jakarta.persistence.IdClass;")

        lines: List[str] = []
        json_converter_sources: List[Tuple[str, str]] = []

        for f in fields:
            col_name = snake_case(f["name"])
            required = f.get("cardinality", {}).get("min", 0) > 0
            nullable = "false" if required else "true"
            field_doc = render_javadoc_block(str(f.get("description", "")) or None, indent="    ").rstrip("\n")
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(java_t, imports)
            for target_struct_id in struct_target_ids_for_type(f["type"]):
                target_struct = struct_by_id[target_struct_id]
                imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

            if f["type"]["kind"] in {"list", "struct"}:
                if f["type"]["kind"] == "list":
                    converter_name = f"{obj['name']}{pascal_case(f['name'])}ListConverter"
                    converter_mode = "list"
                    converter_target_type = java_type_for_type_descriptor(
                        f["type"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                    element_type = java_type_for_type_descriptor(
                        f["type"]["element"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                else:
                    converter_name = f"{obj['name']}{pascal_case(f['name'])}StructConverter"
                    converter_mode = "struct"
                    converter_target_type = java_type_for_type_descriptor(
                        f["type"],
                        type_by_id,
                        object_by_id,
                        struct_by_id,
                    )
                    element_type = converter_target_type
                if field_doc:
                    lines.append(field_doc)
                lines.append(f"    @Convert(converter = {converter_name}.class)")
                lines.append(f"    @Column(name = \"{col_name}\", nullable = {nullable}, columnDefinition = \"text\")")
                lines.append(f"    private {java_t} {camel_case(f['name'])};")
                lines.append("")

                converter_imports = {
                    "import com.fasterxml.jackson.core.JsonProcessingException;",
                    "import com.fasterxml.jackson.databind.ObjectMapper;",
                    "import jakarta.persistence.AttributeConverter;",
                    "import jakarta.persistence.Converter;",
                }
                if converter_mode == "list":
                    converter_imports.add("import com.fasterxml.jackson.core.type.TypeReference;")
                    converter_imports.add("import java.util.Collections;")
                    converter_imports.add("import java.util.List;")
                add_java_imports_for_type(converter_target_type, converter_imports)
                if converter_mode == "list":
                    target_ref_type = f["type"]["element"]
                else:
                    target_ref_type = f["type"]
                for target_id in object_ref_target_ids_for_type(target_ref_type):
                    target = object_by_id[target_id]
                    converter_imports.add(f"import {base_package}.generated.domain.{target['name']}Ref;")
                for target_struct_id in struct_target_ids_for_type(target_ref_type):
                    target_struct = struct_by_id[target_struct_id]
                    converter_imports.add(f"import {base_package}.generated.domain.{target_struct['name']};")

                if converter_mode == "list":
                    converter_src = (
                        f"package {base_package}.generated.persistence;\n\n"
                        + "\n".join(sorted(converter_imports))
                        + "\n\n"
                        + "@Converter\n"
                        + f"public class {converter_name} implements AttributeConverter<{converter_target_type}, String> {{\n\n"
                        + "    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().findAndRegisterModules();\n\n"
                        + "    @Override\n"
                        + f"    public String convertToDatabaseColumn({converter_target_type} attribute) {{\n"
                        + "        if (attribute == null) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + "            return OBJECT_MAPPER.writeValueAsString(attribute);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to serialize list field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n\n"
                        + "    @Override\n"
                        + f"    public {converter_target_type} convertToEntityAttribute(String dbData) {{\n"
                        + "        if (dbData == null || dbData.isBlank()) {\n"
                        + "            return Collections.emptyList();\n"
                        + "        }\n"
                        + "        try {\n"
                        + f"            return OBJECT_MAPPER.readValue(dbData, new TypeReference<{converter_target_type}>() {{}});\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to deserialize list field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n"
                        + "}\n"
                    )
                else:
                    converter_src = (
                        f"package {base_package}.generated.persistence;\n\n"
                        + "\n".join(sorted(converter_imports))
                        + "\n\n"
                        + "@Converter\n"
                        + f"public class {converter_name} implements AttributeConverter<{converter_target_type}, String> {{\n\n"
                        + "    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().findAndRegisterModules();\n\n"
                        + "    @Override\n"
                        + f"    public String convertToDatabaseColumn({converter_target_type} attribute) {{\n"
                        + "        if (attribute == null) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + "            return OBJECT_MAPPER.writeValueAsString(attribute);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to serialize struct field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n\n"
                        + "    @Override\n"
                        + f"    public {converter_target_type} convertToEntityAttribute(String dbData) {{\n"
                        + "        if (dbData == null || dbData.isBlank()) {\n"
                        + "            return null;\n"
                        + "        }\n"
                        + "        try {\n"
                        + f"            return OBJECT_MAPPER.readValue(dbData, {converter_target_type}.class);\n"
                        + "        } catch (JsonProcessingException ex) {\n"
                        + f"            throw new IllegalArgumentException(\"Failed to deserialize struct field {obj['name']}.{f['name']}\", ex);\n"
                        + "        }\n"
                        + "    }\n"
                        + "}\n"
                    )
                json_converter_sources.append((converter_name, converter_src))
            elif f["type"]["kind"] == "object_ref":
                if field_doc:
                    lines.append(field_doc)
                imports.update(
                    {
                        "import jakarta.persistence.FetchType;",
                        "import jakarta.persistence.JoinColumn;",
                        "import jakarta.persistence.ManyToOne;",
                    }
                )
                target = object_by_id[f["type"]["target_object_id"]]
                target_entity = f"{target['name']}Entity"
                target_pk = primary_key_field_for_object(target)
                col_name = f"{col_name}_{snake_case(target_pk['name'])}"
                lines.append(f"    @ManyToOne(fetch = FetchType.LAZY, optional = {nullable})")
                lines.append(f"    @JoinColumn(name = \"{col_name}\", nullable = {nullable})")
                lines.append(f"    private {target_entity} {camel_case(f['name'])};")
                lines.append("")
            else:
                if field_doc:
                    lines.append(field_doc)
                if any(f["id"] == key_field["id"] for key_field in pk_fields):
                    lines.append("    @Id")
                lines.append(f"    @Column(name = \"{col_name}\", nullable = {nullable})")
                lines.append(f"    private {java_t} {camel_case(f['name'])};")
                lines.append("")

        if obj.get("states"):
            imports.update(
                {
                    "import jakarta.persistence.EnumType;",
                    "import jakarta.persistence.Enumerated;",
                    f"import {base_package}.generated.domain.{obj['name']}State;",
                }
            )
            lines.append("    @Enumerated(EnumType.STRING)")
            lines.append("    @Column(name = \"current_state\", nullable = false)")
            lines.append(f"    private {obj['name']}State currentState;")
            lines.append("")

        lines.extend(
            [
                "    @Version",
                "    @Column(name = \"row_version\", nullable = false)",
                "    private long rowVersion;",
                "",
                "    @Column(name = \"created_at\", nullable = false, updatable = false)",
                "    private OffsetDateTime createdAt;",
                "",
                "    @Column(name = \"updated_at\", nullable = false)",
                "    private OffsetDateTime updatedAt;",
                "",
                "    @PrePersist",
                "    void onCreate() {",
                "        OffsetDateTime now = OffsetDateTime.now();",
                "        createdAt = now;",
                "        updatedAt = now;",
                "    }",
                "",
                "    @PreUpdate",
                "    void onUpdate() {",
                "        updatedAt = OffsetDateTime.now();",
                "    }",
                "",
            ]
        )

        for f in fields:
            java_t = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            name = camel_case(f["name"])
            method = name[:1].upper() + name[1:]
            lines.append(f"    public {java_t if f['type']['kind'] != 'object_ref' else object_by_id[f['type']['target_object_id']]['name'] + 'Entity'} get{method}() {{")
            lines.append(f"        return {name};")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void set{method}({java_t if f['type']['kind'] != 'object_ref' else object_by_id[f['type']['target_object_id']]['name'] + 'Entity'} {name}) {{")
            lines.append(f"        this.{name} = {name};")
            lines.append("    }")
            lines.append("")

        if obj.get("states"):
            lines.append(f"    public {obj['name']}State getCurrentState() {{")
            lines.append("        return currentState;")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void setCurrentState({obj['name']}State currentState) {{")
            lines.append("        this.currentState = currentState;")
            lines.append("    }")
            lines.append("")

        imports_block = "\n".join(sorted(imports))
        id_class_annotation = f"@IdClass({obj['name']}Key.class)\n" if composite_pk else ""
        entity_src = (
            f"package {base_package}.generated.persistence;\n\n"
            f"{imports_block}\n\n"
            + render_javadoc_block(str(obj.get("description", "")) or None)
            + "@Entity\n"
            + f"@Table(name = \"{table_name}\")\n"
            + id_class_annotation
            + f"public class {entity_name} {{\n\n"
            + "\n".join(lines)
            + "}\n"
        )

        files[f"src/main/java/{package_path}/generated/persistence/{entity_name}.java"] = entity_src
        for converter_name, converter_src in json_converter_sources:
            files[f"src/main/java/{package_path}/generated/persistence/{converter_name}.java"] = converter_src

        if composite_pk:
            key_imports: set[str] = {
                "import java.io.Serializable;",
                "import java.util.Objects;",
            }
            key_fields: List[Tuple[str, str, bool]] = []
            key_member_lines: List[str] = []
            for key_field in pk_fields:
                key_java = java_type_for_field(key_field, type_by_id, object_by_id, struct_by_id)
                key_name = camel_case(key_field["name"])
                add_java_imports_for_type(key_java, key_imports)
                key_fields.append((key_java, key_name, True))
                key_member_lines.append(f"    private {key_java} {key_name};")
            ctor_args = ", ".join(f"{java_t} {name}" for java_t, name, _ in key_fields)
            ctor_assigns = "\n".join(f"        this.{name} = {name};" for _, name, _ in key_fields)
            equals_checks = " && ".join(f"Objects.equals({name}, that.{name})" for _, name, _ in key_fields) or "true"
            hash_args = ", ".join(name for _, name, _ in key_fields)
            accessor_lines: List[str] = []
            for java_t, name, _ in key_fields:
                method = name[:1].upper() + name[1:]
                accessor_lines.extend(
                    [
                        f"    public {java_t} get{method}() {{",
                        f"        return {name};",
                        "    }",
                        "",
                        f"    public void set{method}({java_t} {name}) {{",
                        f"        this.{name} = {name};",
                        "    }",
                        "",
                    ]
                )
            key_src = (
                f"package {base_package}.generated.persistence;\n\n"
                + "\n".join(sorted(key_imports))
                + "\n\n"
                + f"public class {obj['name']}Key implements Serializable {{\n\n"
                + ("\n".join(key_member_lines) + "\n\n" if key_member_lines else "")
                + f"    public {obj['name']}Key() {{\n"
                + "    }\n\n"
                + f"    public {obj['name']}Key({ctor_args}) {{\n"
                + (ctor_assigns + "\n" if ctor_assigns else "")
                + "    }\n\n"
                + "\n".join(accessor_lines)
                + "    @Override\n"
                + "    public boolean equals(Object o) {\n"
                + "        if (this == o) {\n"
                + "            return true;\n"
                + "        }\n"
                + f"        if (!(o instanceof {obj['name']}Key that)) {{\n"
                + "            return false;\n"
                + "        }\n"
                + f"        return {equals_checks};\n"
                + "    }\n\n"
                + "    @Override\n"
                + "    public int hashCode() {\n"
                + f"        return Objects.hash({hash_args});\n"
                + "    }\n"
                + "}\n"
            )
            files[f"src/main/java/{package_path}/generated/persistence/{obj['name']}Key.java"] = key_src
            pk_java = f"{obj['name']}Key"
        else:
            pk_java = java_type_for_field(pk, type_by_id, object_by_id, struct_by_id)
        repo_src = (
            f"package {base_package}.generated.persistence;\n\n"
            "import org.springframework.data.jpa.repository.JpaRepository;\n\n"
            "import org.springframework.data.jpa.repository.JpaSpecificationExecutor;\n\n"
            f"public interface {obj['name']}Repository extends JpaRepository<{entity_name}, {pk_java}>, JpaSpecificationExecutor<{entity_name}> {{\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/persistence/{obj['name']}Repository.java"] = repo_src

        if obj.get("states") and not composite_pk:
            history_entity_name = f"{obj['name']}StateHistoryEntity"
            history_repo_name = f"{obj['name']}StateHistoryRepository"
            pk_col = snake_case(pk["name"])
            history_table = f"{snake_case(obj['name'])}_state_history"
            history_entity = (
                f"package {base_package}.generated.persistence;\n\n"
                "import jakarta.persistence.Column;\n"
                "import jakarta.persistence.Entity;\n"
                "import jakarta.persistence.FetchType;\n"
                "import jakarta.persistence.GeneratedValue;\n"
                "import jakarta.persistence.GenerationType;\n"
                "import jakarta.persistence.Id;\n"
                "import jakarta.persistence.JoinColumn;\n"
                "import jakarta.persistence.ManyToOne;\n"
                "import jakarta.persistence.PrePersist;\n"
                "import jakarta.persistence.Table;\n"
                "import java.time.OffsetDateTime;\n\n"
                "@Entity\n"
                f"@Table(name = \"{history_table}\")\n"
                f"public class {history_entity_name} {{\n\n"
                "    @Id\n"
                "    @GeneratedValue(strategy = GenerationType.IDENTITY)\n"
                "    @Column(name = \"history_id\")\n"
                "    private Long historyId;\n\n"
                "    @ManyToOne(fetch = FetchType.LAZY, optional = false)\n"
                f"    @JoinColumn(name = \"{pk_col}\", nullable = false)\n"
                f"    private {obj['name']}Entity {camel_case(obj['name'])};\n\n"
                "    @Column(name = \"transition_id\", nullable = false)\n"
                "    private String transitionId;\n\n"
                "    @Column(name = \"from_state\", nullable = false)\n"
                "    private String fromState;\n\n"
                "    @Column(name = \"to_state\", nullable = false)\n"
                "    private String toState;\n\n"
                "    @Column(name = \"changed_at\", nullable = false)\n"
                "    private OffsetDateTime changedAt;\n\n"
                "    @Column(name = \"changed_by\")\n"
                "    private String changedBy;\n\n"
                "    @PrePersist\n"
                "    void onCreate() {\n"
                "        if (changedAt == null) {\n"
                "            changedAt = OffsetDateTime.now();\n"
                "        }\n"
                "    }\n\n"
                f"    public void set{obj['name']}({obj['name']}Entity value) {{\n"
                f"        this.{camel_case(obj['name'])} = value;\n"
                "    }\n\n"
                "    public void setTransitionId(String transitionId) {\n"
                "        this.transitionId = transitionId;\n"
                "    }\n\n"
                "    public void setFromState(String fromState) {\n"
                "        this.fromState = fromState;\n"
                "    }\n\n"
                "    public void setToState(String toState) {\n"
                "        this.toState = toState;\n"
                "    }\n\n"
                "    public void setChangedBy(String changedBy) {\n"
                "        this.changedBy = changedBy;\n"
                "    }\n"
                "}\n"
            )
            files[f"src/main/java/{package_path}/generated/persistence/{history_entity_name}.java"] = history_entity
            history_repo = (
                f"package {base_package}.generated.persistence;\n\n"
                "import org.springframework.data.jpa.repository.JpaRepository;\n\n"
                f"public interface {history_repo_name} extends JpaRepository<{history_entity_name}, Long> {{\n"
                "}\n"
            )
            files[f"src/main/java/{package_path}/generated/persistence/{history_repo_name}.java"] = history_repo

    config_src = (
        f"package {base_package}.generated.config;\n\n"
        "import org.springframework.boot.autoconfigure.domain.EntityScan;\n"
        "import org.springframework.context.annotation.Configuration;\n"
        "import org.springframework.data.jpa.repository.config.EnableJpaRepositories;\n\n"
        "@Configuration\n"
        f"@EntityScan(basePackages = \"{base_package}.generated.persistence\")\n"
        f"@EnableJpaRepositories(basePackages = \"{base_package}.generated.persistence\")\n"
        "public class GeneratedPersistenceConfig {\n"
        "}\n"
    )
    files[f"src/main/java/{package_path}/generated/config/GeneratedPersistenceConfig.java"] = config_src
