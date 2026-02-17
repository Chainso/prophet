from __future__ import annotations

from typing import Any, Dict, List

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.codegen.rendering import primary_key_fields_for_object


def _state_name_by_id(obj: Dict[str, Any]) -> Dict[str, str]:
    return {
        str(state.get("id", "")): str(state.get("name", ""))
        for state in obj.get("states", [])
        if isinstance(state, dict)
    }


def render_transition_runtime_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    objects = state["objects"]
    events = state["events"]
    object_by_id = state["object_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]

    transition_events = [
        event
        for event in sorted(events, key=lambda item: str(item.get("id", "")))
        if isinstance(event, dict) and str(event.get("kind", "")) == "transition"
    ]
    if not transition_events:
        return

    transition_event_by_transition_id: Dict[str, Dict[str, Any]] = {}
    for event in transition_events:
        transition_id = str(event.get("transition_id", ""))
        if transition_id:
            transition_event_by_transition_id[transition_id] = event

    for event in transition_events:
        event_name = str(event.get("name", "TransitionEvent"))
        draft_name = f"{event_name}Draft"
        draft_src = (
            f"package {base_package}.generated.events;\n\n"
            + f"public final class {draft_name} {{\n"
            + f"    private final {event_name}.Builder builder;\n\n"
            + f"    public {draft_name}({event_name}.Builder builder) {{\n"
            + "        this.builder = builder;\n"
            + "    }\n\n"
            + f"    public {event_name}.Builder builder() {{\n"
            + "        return builder;\n"
            + "    }\n\n"
            + f"    public {event_name} build() {{\n"
            + "        return builder.build();\n"
            + "    }\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/events/{draft_name}.java"] = draft_src

    for obj in sorted(objects, key=lambda item: str(item.get("id", ""))):
        if not isinstance(obj, dict):
            continue
        transitions = sorted(
            [item for item in obj.get("transitions", []) if isinstance(item, dict)],
            key=lambda item: str(item.get("id", "")),
        )
        if not transitions:
            continue
        object_id = str(obj.get("id", ""))
        object_name = str(obj.get("name", "Object"))
        object_ref_or_object_name = f"{object_name}RefOrObject"
        object_ref_name = f"{object_name}Ref"
        pk_fields = primary_key_fields_for_object(obj)
        state_by_id = _state_name_by_id(obj)

        handler_name = f"{object_name}TransitionHandler"
        service_name = f"{object_name}TransitionService"
        validator_name = f"{object_name}TransitionValidator"
        validator_default_name = f"{object_name}TransitionValidatorDefault"

        validator_imports = [
            f"package {base_package}.generated.transitions.validators;",
            "",
            f"import {base_package}.generated.domain.{object_name};",
            "import io.prophet.events.runtime.TransitionValidationResult;",
            "",
        ]
        validator_methods: List[str] = []
        validator_default_methods: List[str] = []
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            transition_method_name = camel_case(f"{transition.get('name', 'transition')}_{object_name}")
            validator_method_name = f"validate{pascal_case(transition_method_name)}"
            validator_methods.append(
                f"    TransitionValidationResult {validator_method_name}({object_name} target);"
            )
            validator_default_methods.extend(
                [
                    "    @Override",
                    f"    public TransitionValidationResult {validator_method_name}({object_name} target) {{",
                    "        return TransitionValidationResult.passed();",
                    "    }",
                    "",
                ]
            )
        if not validator_methods:
            continue

        validator_src = (
            "\n".join(validator_imports)
            + f"public interface {validator_name} {{\n"
            + "\n".join(validator_methods)
            + "\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/transitions/validators/{validator_name}.java"] = validator_src

        validator_default_src = (
            f"package {base_package}.generated.transitions.validators.defaults;\n\n"
            + f"import {base_package}.generated.domain.{object_name};\n"
            + f"import {base_package}.generated.transitions.validators.{validator_name};\n"
            + "import io.prophet.events.runtime.TransitionValidationResult;\n\n"
            + "@org.springframework.stereotype.Component\n"
            + f"@org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean(value = {validator_name}.class, ignored = {validator_default_name}.class)\n"
            + f"public class {validator_default_name} implements {validator_name} {{\n"
            + "\n".join(validator_default_methods)
            + "}\n"
        )
        files[
            f"src/main/java/{package_path}/generated/transitions/validators/defaults/{validator_default_name}.java"
        ] = validator_default_src

        handler_lines: List[str] = [
            f"package {base_package}.generated.transitions.handlers;",
            "",
            f"import {base_package}.generated.domain.{object_ref_or_object_name};",
        ]
        method_lines: List[str] = []
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            event_name = str(event.get("name", "TransitionEvent"))
            draft_name = f"{event_name}Draft"
            handler_lines.append(f"import {base_package}.generated.events.{draft_name};")
            method_name = camel_case(f"{transition.get('name', 'transition')}_{object_name}")
            method_lines.append(f"    {draft_name} {method_name}({object_ref_or_object_name} target);")
        if not method_lines:
            continue
        handler_src = (
            "\n".join(handler_lines)
            + "\n\n"
            + f"public interface {handler_name} {{\n"
            + "\n".join(method_lines)
            + "\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/transitions/handlers/{handler_name}.java"] = handler_src

        default_imports: List[str] = [
            f"import {base_package}.generated.domain.{object_name};",
            f"import {base_package}.generated.domain.{object_ref_name};",
            f"import {base_package}.generated.domain.{object_ref_or_object_name};",
            f"import {base_package}.generated.domain.{object_name}State;",
            f"import {base_package}.generated.mapping.{object_name}DomainMapper;",
            f"import {base_package}.generated.persistence.{object_name}Entity;",
            f"import {base_package}.generated.persistence.{object_name}Repository;",
            f"import {base_package}.generated.transitions.handlers.{handler_name};",
            f"import {base_package}.generated.transitions.validators.{validator_name};",
            "import io.prophet.events.runtime.TransitionValidationResult;",
            "import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;",
            "import org.springframework.stereotype.Component;",
        ]

        default_fields: List[str] = [
            f"    private final {object_name}Repository repository;",
            f"    private final {object_name}DomainMapper mapper;",
            f"    private final {validator_name} validator;",
        ]
        ctor_args: List[str] = [
            f"        {object_name}Repository repository",
            f"        {object_name}DomainMapper mapper",
            f"        {validator_name} validator",
        ]
        ctor_assigns: List[str] = [
            "        this.repository = repository;",
            "        this.mapper = mapper;",
            "        this.validator = validator;",
        ]

        supports_history = len(pk_fields) == 1
        if supports_history:
            default_imports.append(f"import {base_package}.generated.persistence.{object_name}StateHistoryEntity;")
            default_imports.append(f"import {base_package}.generated.persistence.{object_name}StateHistoryRepository;")
            default_fields.append(f"    private final {object_name}StateHistoryRepository historyRepository;")
            ctor_args.append(f"        {object_name}StateHistoryRepository historyRepository")
            ctor_assigns.append("        this.historyRepository = historyRepository;")

        method_impls: List[str] = []
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            event_name = str(event.get("name", "TransitionEvent"))
            draft_name = f"{event_name}Draft"
            default_imports.append(f"import {base_package}.generated.events.{event_name};")
            default_imports.append(f"import {base_package}.generated.events.{draft_name};")

            from_state_name = state_by_id.get(str(transition.get("from_state_id", "")), "")
            to_state_name = state_by_id.get(str(transition.get("to_state_id", "")), "")
            from_state_enum = from_state_name.upper()
            to_state_enum = to_state_name.upper()
            method_name = camel_case(f"{transition.get('name', 'transition')}_{object_name}")
            validator_method_name = f"validate{pascal_case(method_name)}"

            key_build_lines: List[str] = []
            find_by_id_expr = ""
            if len(pk_fields) == 1:
                pk = pk_fields[0]
                pk_prop = camel_case(str(pk.get("name", "id")))
                key_build_lines.extend(
                    [
                        f"        var {pk_prop} = target instanceof {object_ref_name} ref ? ref.{pk_prop}() : (({object_name}) target).{pk_prop}();",
                    ]
                )
                find_by_id_expr = pk_prop
            else:
                key_class = f"{object_name}Key"
                default_imports.append(f"import {base_package}.generated.persistence.{key_class};")
                for pk in pk_fields:
                    pk_prop = camel_case(str(pk.get("name", "id")))
                    key_build_lines.append(
                        f"        var {pk_prop} = target instanceof {object_ref_name} ref ? ref.{pk_prop}() : (({object_name}) target).{pk_prop}();"
                    )
                key_build_lines.append(f"        {key_class} key = new {key_class}();")
                for pk in pk_fields:
                    pk_prop = camel_case(str(pk.get("name", "id")))
                    key_build_lines.append(f"        key.set{pascal_case(pk_prop)}({pk_prop});")
                find_by_id_expr = "key"

            builder_lines = [
                f"        {event_name}.Builder builder = {event_name}.builder()",
            ]
            pk_prop_names = {
                camel_case(str(field.get("name", "id")))
                for field in pk_fields
            }
            for field in [item for item in event.get("fields", []) if isinstance(item, dict)]:
                field_name = str(field.get("name", "field"))
                prop = camel_case(field_name)
                if field_name == "fromState":
                    builder_lines.append(f"            .{prop}(\"{from_state_name}\")")
                elif field_name == "toState":
                    builder_lines.append(f"            .{prop}(\"{to_state_name}\")")
                elif prop in pk_prop_names:
                    builder_lines.append(f"            .{prop}({prop})")
            builder_lines[-1] = builder_lines[-1] + ";"

            history_lines: List[str] = []
            if supports_history:
                history_lines = [
                    f"        {object_name}StateHistoryEntity history = new {object_name}StateHistoryEntity();",
                    f"        history.set{object_name}(entity);",
                    f"        history.setTransitionId(\"{transition_id}\");",
                    f"        history.setFromState(\"{from_state_name}\");",
                    f"        history.setToState(\"{to_state_name}\");",
                    "        historyRepository.save(history);",
                ]

            method_body = [
                "    @Override",
                f"    public {draft_name} {method_name}({object_ref_or_object_name} target) {{",
                *key_build_lines,
                f"        {object_name}Entity entity = repository.findById({find_by_id_expr})",
                f"            .orElseThrow(() -> new IllegalStateException(\"{object_name} not found for transition '{transition.get('name', 'transition')}'\"));",
                f"        if (entity.getState() != {object_name}State.{from_state_enum}) {{",
                f"            throw new IllegalStateException(\"Invalid state transition {object_name}.{transition.get('name', 'transition')}: expected {from_state_name} but was \" + entity.getState());",
                "        }",
                f"        {object_name} current = mapper.toDomain(entity);",
                f"        TransitionValidationResult validation = validator.{validator_method_name}(current);",
                "        if (!validation.passesValidation()) {",
                f"            throw new IllegalStateException(validation.failureReason() == null || validation.failureReason().isBlank() ? \"Transition validation failed for {object_name}.{transition.get('name', 'transition')}\" : validation.failureReason());",
                "        }",
                f"        entity.setState({object_name}State.{to_state_enum});",
                "        entity = repository.save(entity);",
                *history_lines,
                *builder_lines,
                f"        return new {draft_name}(builder);",
                "    }",
                "",
            ]
            method_impls.extend(method_body)

        default_src = (
            f"package {base_package}.generated.transitions.handlers.defaults;\n\n"
            + "\n".join(sorted(dict.fromkeys(default_imports)))
            + "\n\n"
            + "@Component\n"
            + f"@ConditionalOnMissingBean(value = {handler_name}.class, ignored = {handler_name}Default.class)\n"
            + f"public class {handler_name}Default implements {handler_name} {{\n"
            + "\n".join(default_fields)
            + "\n\n"
            + f"    public {handler_name}Default(\n"
            + ",\n".join(ctor_args)
            + "\n"
            + "    ) {\n"
            + "\n".join(ctor_assigns)
            + "\n"
            + "    }\n\n"
            + "\n".join(method_impls)
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/transitions/handlers/defaults/{handler_name}Default.java"] = default_src

        service_imports = {
            f"import {base_package}.generated.domain.{object_ref_or_object_name};",
        }
        service_methods: List[str] = []
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            event_name = str(event.get("name", "TransitionEvent"))
            draft_name = f"{event_name}Draft"
            service_imports.add(f"import {base_package}.generated.events.{draft_name};")
            method_name = camel_case(f"{transition.get('name', 'transition')}_{object_name}")
            service_methods.append(f"    {draft_name} {method_name}({object_ref_or_object_name} target);")

        service_src = (
            f"package {base_package}.generated.transitions.services;\n\n"
            + "\n".join(sorted(service_imports))
            + "\n\n"
            + f"public interface {service_name} {{\n"
            + "\n".join(service_methods)
            + "\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/transitions/services/{service_name}.java"] = service_src

        service_default_imports = {
            f"import {base_package}.generated.domain.{object_ref_or_object_name};",
            f"import {base_package}.generated.transitions.handlers.{handler_name};",
            f"import {base_package}.generated.transitions.services.{service_name};",
            "import org.springframework.beans.factory.ObjectProvider;",
            "import org.springframework.stereotype.Component;",
        }
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            event_name = str(event.get("name", "TransitionEvent"))
            draft_name = f"{event_name}Draft"
            service_default_imports.add(f"import {base_package}.generated.events.{draft_name};")

        service_default_src = (
            f"package {base_package}.generated.transitions.services.defaults;\n\n"
            + "\n".join(sorted(service_default_imports))
            + "\n\n"
            + "@Component\n"
            + f"public class {service_name}Default implements {service_name} {{\n"
            + f"    private final ObjectProvider<{handler_name}> handlerProvider;\n\n"
            + f"    public {service_name}Default(ObjectProvider<{handler_name}> handlerProvider) {{\n"
            + "        this.handlerProvider = handlerProvider;\n"
            + "    }\n\n"
        )
        forwarding_methods: List[str] = []
        for transition in transitions:
            transition_id = str(transition.get("id", ""))
            event = transition_event_by_transition_id.get(transition_id)
            if not event:
                continue
            event_name = str(event.get("name", "TransitionEvent"))
            draft_name = f"{event_name}Draft"
            method_name = camel_case(f"{transition.get('name', 'transition')}_{object_name}")
            forwarding_methods.extend(
                [
                    "    @Override",
                    f"    public {draft_name} {method_name}({object_ref_or_object_name} target) {{",
                    f"        {handler_name} handler = handlerProvider.getIfAvailable();",
                    "        if (handler == null) {",
                    f"            throw new UnsupportedOperationException(\"No transition handler bean provided for object '{object_name}'\");",
                    "        }",
                    f"        return handler.{method_name}(target);",
                    "    }",
                    "",
                ]
            )
        service_default_src += "\n".join(forwarding_methods) + "}\n"
        files[
            f"src/main/java/{package_path}/generated/transitions/services/defaults/{service_name}Default.java"
        ] = service_default_src
