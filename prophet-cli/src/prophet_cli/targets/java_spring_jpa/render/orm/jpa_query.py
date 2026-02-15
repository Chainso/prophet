from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.codegen.rendering import pluralize
from prophet_cli.codegen.rendering import primary_key_field_for_object
from prophet_cli.codegen.rendering import primary_key_fields_for_object
from prophet_cli.codegen.rendering import snake_case
from prophet_cli.targets.java_common.render.support import add_java_imports_for_type
from prophet_cli.targets.java_common.render.support import java_type_for_field
from prophet_cli.targets.java_common.render.support import object_has_composite_primary_key
from prophet_cli.targets.java_common.render.support import render_java_record_with_builder

def render_jpa_query_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    objects = state["objects"]
    type_by_id = state["type_by_id"]
    object_by_id = state["object_by_id"]
    struct_by_id = state["struct_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]

    # object query controllers
    for obj in objects:
        fields = obj.get("fields", [])
        pk_fields = primary_key_fields_for_object(obj)
        pk = pk_fields[0]
        composite_pk = len(pk_fields) > 1
        repo_name = f"{obj['name']}Repository"
        entity_name = f"{obj['name']}Entity"
        domain_name = obj["name"]
        mapper_name = f"{obj['name']}DomainMapper"
        list_response_name = f"{obj['name']}ListResponse"
        pk_prop = camel_case(pk["name"])
        pk_java = java_type_for_field(pk, type_by_id, object_by_id, struct_by_id)
        path_table = pluralize(snake_case(obj["name"]))

        imports = {
            "import java.util.List;",
            "import java.util.Optional;",
            "import org.springframework.data.domain.Page;",
            "import org.springframework.data.domain.Pageable;",
            "import org.springframework.data.jpa.domain.Specification;",
            "import org.springframework.data.web.PageableDefault;",
            "import org.springframework.http.ResponseEntity;",
            "import org.springframework.web.bind.annotation.GetMapping;",
            "import org.springframework.web.bind.annotation.PathVariable;",
            "import org.springframework.web.bind.annotation.RequestMapping;",
            "import org.springframework.web.bind.annotation.RestController;",
            f"import {base_package}.generated.domain.{domain_name};",
            f"import {base_package}.generated.mapping.{mapper_name};",
            f"import {base_package}.generated.persistence.{entity_name};",
            f"import {base_package}.generated.persistence.{repo_name};",
        }
        if composite_pk:
            imports.add(f"import {base_package}.generated.persistence.{obj['name']}Key;")
        add_java_imports_for_type(pk_java, imports)

        ref_imports: set[str] = set()
        domain_builder_steps: List[str] = []
        for f in fields:
            prop = camel_case(f["name"])
            getter = "get" + prop[:1].upper() + prop[1:] + "()"
            if f["type"]["kind"] == "object_ref":
                target = object_by_id[f["type"]["target_object_id"]]
                target_pk = primary_key_field_for_object(target)
                target_pk_prop = camel_case(target_pk["name"])
                target_get = "get" + target_pk_prop[:1].upper() + target_pk_prop[1:] + "()"
                ref_cls = f"{target['name']}Ref"
                ref_imports.add(f"import {base_package}.generated.domain.{ref_cls};")
                domain_builder_steps.append(
                    f"            .{prop}(entity.{getter} == null ? null : {ref_cls}.builder().{target_pk_prop}(entity.{getter}.{target_get}).build())"
                )
            else:
                domain_builder_steps.append(f"            .{prop}(entity.{getter})")

        if obj.get("states"):
            enum_cls = f"{obj['name']}State"
            imports.add(f"import {base_package}.generated.domain.{enum_cls};")
            domain_builder_steps.append("            .currentState(entity.getCurrentState())")

        mapper_imports = {
            "import org.springframework.stereotype.Component;",
            f"import {base_package}.generated.domain.{domain_name};",
            f"import {base_package}.generated.persistence.{entity_name};",
        }
        mapper_imports = mapper_imports.union(ref_imports)
        mapper_src = (
            f"package {base_package}.generated.mapping;\n\n"
            + "\n".join(sorted(mapper_imports))
            + "\n\n"
            + "@Component\n"
            + f"public class {mapper_name} {{\n"
            + f"    public {domain_name} toDomain({entity_name} entity) {{\n"
            + "        if (entity == null) {\n"
            + "            return null;\n"
            + "        }\n"
            + f"        return {domain_name}.builder()\n"
            + "\n".join(domain_builder_steps)
            + "\n            .build();\n"
            + "    }\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/mapping/{mapper_name}.java"] = mapper_src

        list_method_params: List[str] = ["        @PageableDefault(size = 20) Pageable pageable"]
        typed_filter_conditions: List[str] = []
        typed_query_fields: List[Tuple[str, str, bool]] = []
        typed_query_imports: set[str] = set()
        needs_join_type_import = False

        def base_type_for_descriptor(type_desc: Dict[str, Any]) -> Optional[str]:
            if type_desc["kind"] == "base":
                return str(type_desc["name"])
            if type_desc["kind"] == "custom":
                return str(type_by_id[type_desc["target_type_id"]]["base"])
            return None

        for f in fields:
            field_type = f["type"]
            kind = field_type["kind"]
            if kind in {"list", "struct"}:
                continue

            entity_prop = camel_case(f["name"])
            filter_record_name = f"{obj['name']}{pascal_case(entity_prop)}Filter"
            if kind == "object_ref":
                target = object_by_id[field_type["target_object_id"]]
                target_pk = primary_key_field_for_object(target)
                target_pk_prop = camel_case(target_pk["name"])
                param_java = java_type_for_field(target_pk, type_by_id, object_by_id, struct_by_id)
                add_java_imports_for_type(param_java, imports)
                needs_join_type_import = True

                filter_imports: set[str] = set()
                add_java_imports_for_type(param_java, filter_imports)
                filter_imports.add("import java.util.List;")
                filter_fields = [
                    (param_java, "eq", False),
                    (f"List<{param_java}>", "in", False),
                ]
                files[
                    f"src/main/java/{package_path}/generated/api/filters/{filter_record_name}.java"
                ] = render_java_record_with_builder(
                    f"{base_package}.generated.api.filters",
                    filter_imports,
                    filter_record_name,
                    filter_fields,
                )
                typed_query_fields.append((filter_record_name, entity_prop, False))
                typed_query_imports.add(f"import {base_package}.generated.api.filters.{filter_record_name};")
                typed_filter_conditions.extend(
                    [
                        f"            if (filter.{entity_prop}() != null) {{",
                        f"                {filter_record_name} {entity_prop}Filter = filter.{entity_prop}();",
                        f"                if ({entity_prop}Filter.eq() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.equal(root.join(\"{entity_prop}\", JoinType.LEFT).get(\"{target_pk_prop}\"), {entity_prop}Filter.eq()));",
                        "                }",
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.join(\"{entity_prop}\", JoinType.LEFT).get(\"{target_pk_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        "            }",
                    ]
                )
                continue

            param_java = java_type_for_field(f, type_by_id, object_by_id, struct_by_id)
            add_java_imports_for_type(param_java, imports)
            base_type = base_type_for_descriptor(field_type)

            filter_imports: set[str] = set()
            add_java_imports_for_type(param_java, filter_imports)
            filter_fields: List[Tuple[str, str, bool]] = [(param_java, "eq", False)]
            typed_condition_lines = [
                f"            if (filter.{entity_prop}() != null) {{",
                f"                {filter_record_name} {entity_prop}Filter = filter.{entity_prop}();",
                f"                if ({entity_prop}Filter.eq() != null) {{",
                f"                    spec = spec.and((root, query, cb) -> cb.equal(root.get(\"{entity_prop}\"), {entity_prop}Filter.eq()));",
                "                }",
            ]

            if base_type in {"string", "duration"}:
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                filter_fields.append(("String", "contains", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        f"                if ({entity_prop}Filter.contains() != null && !{entity_prop}Filter.contains().isBlank()) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.like(cb.lower(root.<String>get(\"{entity_prop}\")), \"%\" + {entity_prop}Filter.contains().toLowerCase() + \"%\"));",
                        "                }",
                    ]
                )
            elif base_type in {"int", "long", "short", "byte", "double", "float", "decimal", "date", "datetime"}:
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                filter_fields.append((param_java, "gte", False))
                filter_fields.append((param_java, "lte", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                        f"                if ({entity_prop}Filter.gte() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.greaterThanOrEqualTo(root.<{param_java}>get(\"{entity_prop}\"), {entity_prop}Filter.gte()));",
                        "                }",
                        f"                if ({entity_prop}Filter.lte() != null) {{",
                        f"                    spec = spec.and((root, query, cb) -> cb.lessThanOrEqualTo(root.<{param_java}>get(\"{entity_prop}\"), {entity_prop}Filter.lte()));",
                        "                }",
                    ]
                )
            elif base_type != "boolean":
                filter_imports.add("import java.util.List;")
                filter_fields.append((f"List<{param_java}>", "in", False))
                typed_condition_lines.extend(
                    [
                        f"                if ({entity_prop}Filter.in() != null && !{entity_prop}Filter.in().isEmpty()) {{",
                        f"                    spec = spec.and((root, query, cb) -> root.get(\"{entity_prop}\").in({entity_prop}Filter.in()));",
                        "                }",
                    ]
                )

            typed_condition_lines.extend(["            }"])
            files[
                f"src/main/java/{package_path}/generated/api/filters/{filter_record_name}.java"
            ] = render_java_record_with_builder(
                f"{base_package}.generated.api.filters",
                filter_imports,
                filter_record_name,
                filter_fields,
            )
            typed_query_fields.append((filter_record_name, entity_prop, False))
            typed_query_imports.add(f"import {base_package}.generated.api.filters.{filter_record_name};")
            typed_filter_conditions.extend(typed_condition_lines)

        if obj.get("states"):
            enum_cls = f"{obj['name']}State"
            state_filter_name = f"{obj['name']}CurrentStateFilter"
            files[
                f"src/main/java/{package_path}/generated/api/filters/{state_filter_name}.java"
            ] = render_java_record_with_builder(
                f"{base_package}.generated.api.filters",
                {
                    "import java.util.List;",
                    f"import {base_package}.generated.domain.{enum_cls};",
                },
                state_filter_name,
                [(enum_cls, "eq", False), (f"List<{enum_cls}>", "in", False)],
            )
            typed_query_fields.append((state_filter_name, "currentState", False))
            typed_query_imports.add(f"import {base_package}.generated.api.filters.{state_filter_name};")
            typed_filter_conditions.extend(
                [
                    "            if (filter.currentState() != null) {",
                    f"                {state_filter_name} currentStateFilter = filter.currentState();",
                    "                if (currentStateFilter.eq() != null) {",
                    "                    spec = spec.and((root, query, cb) -> cb.equal(root.get(\"currentState\"), currentStateFilter.eq()));",
                    "                }",
                    "                if (currentStateFilter.in() != null && !currentStateFilter.in().isEmpty()) {",
                    "                    spec = spec.and((root, query, cb) -> root.get(\"currentState\").in(currentStateFilter.in()));",
                    "                }",
                    "            }",
                ]
            )

        typed_query_name = f"{obj['name']}QueryFilter"
        files[
            f"src/main/java/{package_path}/generated/api/filters/{typed_query_name}.java"
        ] = render_java_record_with_builder(
            f"{base_package}.generated.api.filters",
            typed_query_imports,
            typed_query_name,
            typed_query_fields,
        )
        imports = imports.union(typed_query_imports)
        imports.add("import org.springframework.web.bind.annotation.PostMapping;")
        imports.add("import org.springframework.web.bind.annotation.RequestBody;")
        imports.add(f"import {base_package}.generated.api.filters.{typed_query_name};")

        list_method_signature = ",\n".join(list_method_params)

        if needs_join_type_import:
            imports.add("import jakarta.persistence.criteria.JoinType;")

        list_response_src = render_java_record_with_builder(
            f"{base_package}.generated.api",
            {
                "import java.util.List;",
                f"import {base_package}.generated.domain.{domain_name};",
            },
            list_response_name,
            [
                (f"List<{domain_name}>", "items", True),
                ("int", "page", True),
                ("int", "size", True),
                ("long", "totalElements", True),
                ("int", "totalPages", True),
            ],
        )
        files[f"src/main/java/{package_path}/generated/api/{list_response_name}.java"] = list_response_src

        typed_filter_block = "\n".join(typed_filter_conditions)
        typed_query_method = (
            "    @PostMapping(\"/query\")\n"
            f"    public ResponseEntity<{list_response_name}> query(\n"
            f"        @RequestBody(required = false) {typed_query_name} filter,\n"
            "        @PageableDefault(size = 20) Pageable pageable\n"
            "    ) {\n"
            f"        Specification<{entity_name}> spec = (root, query, cb) -> cb.conjunction();\n"
            "        if (filter != null) {\n"
            + (typed_filter_block + "\n" if typed_filter_block else "")
            + "        }\n"
            + f"        Page<{entity_name}> entityPage = repository.findAll(spec, pageable);\n"
            + f"        List<{domain_name}> items = entityPage.stream().map(mapper::toDomain).toList();\n"
            + f"        {list_response_name} result = {list_response_name}.builder()\n"
            + "            .items(items)\n"
            + "            .page(entityPage.getNumber())\n"
            + "            .size(entityPage.getSize())\n"
            + "            .totalElements(entityPage.getTotalElements())\n"
            + "            .totalPages(entityPage.getTotalPages())\n"
            + "            .build();\n"
            + "        return ResponseEntity.ok(result);\n"
            + "    }\n\n"
        )

        get_by_id_method = ""
        if composite_pk:
            key_path_parts: List[str] = []
            key_param_decls: List[str] = []
            key_ctor_args: List[str] = []
            for key_field in pk_fields:
                key_name = camel_case(key_field["name"])
                key_java = java_type_for_field(key_field, type_by_id, object_by_id, struct_by_id)
                add_java_imports_for_type(key_java, imports)
                key_path_parts.append(f"{{{key_name}}}")
                key_param_decls.append(f"@PathVariable(\"{key_name}\") {key_java} {key_name}")
                key_ctor_args.append(key_name)
            key_path = "/".join(key_path_parts)
            key_params = ", ".join(key_param_decls)
            key_ctor = ", ".join(key_ctor_args)
            get_by_id_method = (
                f"    @GetMapping(\"/{key_path}\")\n"
                f"    public ResponseEntity<{domain_name}> getById({key_params}) {{\n"
                f"        {obj['name']}Key key = new {obj['name']}Key({key_ctor});\n"
                f"        Optional<{entity_name}> maybeEntity = repository.findById(key);\n"
                "        if (maybeEntity.isEmpty()) {\n"
                "            return ResponseEntity.notFound().build();\n"
                "        }\n\n"
                f"        {domain_name} domain = mapper.toDomain(maybeEntity.get());\n"
                "        return ResponseEntity.ok(domain);\n"
                "    }\n"
            )
        else:
            get_by_id_method = (
                f"    @GetMapping(\"/{{{pk_prop}}}\")\n"
                f"    public ResponseEntity<{domain_name}> getById(@PathVariable(\"{pk_prop}\") {pk_java} {pk_prop}) {{\n"
                f"        Optional<{entity_name}> maybeEntity = repository.findById({pk_prop});\n"
                "        if (maybeEntity.isEmpty()) {\n"
                "            return ResponseEntity.notFound().build();\n"
                "        }\n\n"
                f"        {domain_name} domain = mapper.toDomain(maybeEntity.get());\n"
                "        return ResponseEntity.ok(domain);\n"
                "    }\n"
            )

        imports_block = "\n".join(sorted(imports))
        query_src = (
            f"package {base_package}.generated.api;\n\n"
            f"{imports_block}\n\n"
            "@RestController\n"
            f"@RequestMapping(\"/{path_table}\")\n"
            f"public class {obj['name']}QueryController {{\n\n"
            f"    private final {repo_name} repository;\n"
            f"    private final {mapper_name} mapper;\n\n"
            f"    public {obj['name']}QueryController({repo_name} repository, {mapper_name} mapper) {{\n"
            "        this.repository = repository;\n"
            "        this.mapper = mapper;\n"
            "    }\n\n"
            "    @GetMapping\n"
            f"    public ResponseEntity<{list_response_name}> list(\n"
            f"{list_method_signature}\n"
            "    ) {\n"
            f"        Specification<{entity_name}> spec = (root, query, cb) -> cb.conjunction();\n"
            + f"        Page<{entity_name}> entityPage = repository.findAll(spec, pageable);\n"
            + f"        List<{domain_name}> items = entityPage.stream().map(mapper::toDomain).toList();\n"
            + f"        {list_response_name} result = {list_response_name}.builder()\n"
            + "            .items(items)\n"
            + "            .page(entityPage.getNumber())\n"
            + "            .size(entityPage.getSize())\n"
            + "            .totalElements(entityPage.getTotalElements())\n"
            + "            .totalPages(entityPage.getTotalPages())\n"
            + "            .build();\n"
            + "        return ResponseEntity.ok(result);\n"
            + "    }\n\n"
            + typed_query_method
            + get_by_id_method
            + "}\n"
        )

        files[f"src/main/java/{package_path}/generated/api/{obj['name']}QueryController.java"] = query_src

