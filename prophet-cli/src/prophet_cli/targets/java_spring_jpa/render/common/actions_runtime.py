from __future__ import annotations

from typing import Any, Dict, List

from prophet_cli.codegen.rendering import camel_case
from prophet_cli.codegen.rendering import pascal_case
from prophet_cli.targets.java_common.render.support import render_javadoc_block


def render_action_runtime_artifacts(files: Dict[str, str], state: Dict[str, Any]) -> None:
    actions = state["actions"]
    action_input_by_id = state["action_input_by_id"]
    event_by_id = state["event_by_id"]
    base_package = state["base_package"]
    package_path = state["package_path"]
    default_event_source = str(state.get("ontology_name", "prophet"))

    # action handler interfaces
    for action in sorted(actions, key=lambda x: x["id"]):
        req_name = pascal_case(str(action_input_by_id[action["input_shape_id"]]["name"])) or "ActionInput"
        output_event = event_by_id[action["output_event_id"]]
        res_name = pascal_case(str(output_event["name"])) or "Event"
        handler_name = f"{pascal_case(action['name'])}ActionHandler"
        service_name = f"{pascal_case(action['name'])}ActionService"
        action_description = str(action.get("description", "")) or None
        handler_src = (
            f"package {base_package}.generated.actions.handlers;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.events.{res_name};\n"
            f"import {base_package}.generated.events.ActionOutcome;\n"
            f"import {base_package}.generated.events.ActionOutcomes;\n\n"
            + render_javadoc_block(action_description)
            + f"public interface {handler_name} {{\n"
            + f"    {res_name} handle({req_name} request);\n\n"
            + f"    default ActionOutcome<{res_name}> handleOutcome({req_name} request) {{\n"
            + "        return ActionOutcomes.just(handle(request));\n"
            + "    }\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/handlers/{handler_name}.java"] = handler_src

        default_cls = f"{handler_name}Default"
        default_handler_src = (
            f"package {base_package}.generated.actions.handlers.defaults;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.events.{res_name};\n"
            f"import {base_package}.generated.actions.handlers.{handler_name};\n"
            "import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;\n"
            "import org.springframework.stereotype.Component;\n\n"
            "@Component\n"
            f"@ConditionalOnMissingBean({handler_name}.class)\n"
            f"public class {default_cls} implements {handler_name} {{\n"
            "    @Override\n"
            f"    public {res_name} handle({req_name} request) {{\n"
            f"        throw new UnsupportedOperationException(\"Action '{action['name']}' is not implemented\");\n"
            "    }\n"
            "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/handlers/defaults/{default_cls}.java"] = default_handler_src

        service_src = (
            f"package {base_package}.generated.actions.services;\n\n"
            f"import {base_package}.generated.actions.{req_name};\n"
            f"import {base_package}.generated.events.{res_name};\n\n"
            + render_javadoc_block(action_description)
            + f"public interface {service_name} {{\n"
            + f"    {res_name} execute({req_name} request);\n"
            + "}\n"
        )
        files[f"src/main/java/{package_path}/generated/actions/services/{service_name}.java"] = service_src

        default_service_name = f"{service_name}Default"
        primary_event_wrapper = f"{res_name}Event"
        service_default_imports = {
            f"import {base_package}.generated.actions.{req_name};",
            f"import {base_package}.generated.events.{res_name};",
            f"import {base_package}.generated.actions.handlers.{handler_name};",
            f"import {base_package}.generated.actions.services.{service_name};",
            f"import {base_package}.generated.events.ActionOutcome;",
            f"import {base_package}.generated.events.DomainEvent;",
            f"import {base_package}.generated.events.EventPublishingSupport;",
            f"import {base_package}.generated.events.{primary_event_wrapper};",
            "import io.prophet.events.runtime.EventPublisher;",
            "import io.prophet.events.runtime.EventIds;",
            "import java.util.ArrayList;",
            "import java.util.List;",
            "import org.springframework.beans.factory.ObjectProvider;",
            "import org.springframework.stereotype.Component;",
        }

        emit_lines: List[str] = [
            f"        ActionOutcome<{res_name}> outcome = handler.handleOutcome(request);",
            "        List<DomainEvent> events = new ArrayList<>();",
        ]
        emit_lines.append(f"        events.add(new {primary_event_wrapper}(outcome.output()));")
        emit_lines.extend(
            [
                "        events.addAll(outcome.additionalEvents());",
                "        EventPublishingSupport.publishAll(",
                "            eventPublisher,",
                "            events,",
                "            EventIds.createEventId(),",
                f"            \"{default_event_source}\",",
                "            null",
                "        ).toCompletableFuture().join();",
            ]
        )
        emit_section = "\n".join(emit_lines)

        default_service_src = (
            f"package {base_package}.generated.actions.services.defaults;\n\n"
            + "\n".join(sorted(service_default_imports))
            + "\n\n"
            + "@Component\n"
            + f"public class {default_service_name} implements {service_name} {{\n"
            + f"    private final ObjectProvider<{handler_name}> handlerProvider;\n"
            + "    private final EventPublisher eventPublisher;\n\n"
            + f"    public {default_service_name}(\n"
            + f"        ObjectProvider<{handler_name}> handlerProvider,\n"
            + "        EventPublisher eventPublisher\n"
            + "    ) {\n"
            + "        this.handlerProvider = handlerProvider;\n"
            + "        this.eventPublisher = eventPublisher;\n"
            + "    }\n\n"
            + "    @Override\n"
            + f"    public {res_name} execute({req_name} request) {{\n"
            + f"        {handler_name} handler = handlerProvider.getIfAvailable();\n"
            + "        if (handler == null) {\n"
            + f"            throw new UnsupportedOperationException(\"No handler bean provided for action '{action['name']}'\");\n"
            + "        }\n"
            + emit_section
            + "\n"
            + "        return outcome.output();\n"
            + "    }\n"
            + "}\n"
        )
        files[
            f"src/main/java/{package_path}/generated/actions/services/defaults/{default_service_name}.java"
        ] = default_service_src

    # action controller delegates to generated action services
    controller_imports = {
        "import jakarta.validation.Valid;",
        "import org.springframework.http.ResponseEntity;",
        "import org.springframework.web.bind.annotation.PostMapping;",
        "import org.springframework.web.bind.annotation.RequestBody;",
        "import org.springframework.web.bind.annotation.RequestMapping;",
        "import org.springframework.web.bind.annotation.RestController;",
        "import org.springframework.web.server.ResponseStatusException;",
        "import static org.springframework.http.HttpStatus.NOT_IMPLEMENTED;",
    }
    controller_fields: List[str] = []
    ctor_args: List[str] = []
    ctor_assigns: List[str] = []
    controller_methods: List[str] = []
    for action in sorted(actions, key=lambda x: x["id"]):
        req_name = pascal_case(str(action_input_by_id[action["input_shape_id"]]["name"])) or "ActionInput"
        output_event = event_by_id[action["output_event_id"]]
        res_name = pascal_case(str(output_event["name"])) or "Event"
        service_name = f"{pascal_case(action['name'])}ActionService"
        service_var = f"{camel_case(action['name'])}Service"
        method_name = camel_case(action["name"])
        controller_imports.add(f"import {base_package}.generated.actions.{req_name};")
        controller_imports.add(f"import {base_package}.generated.events.{res_name};")
        controller_imports.add(f"import {base_package}.generated.actions.services.{service_name};")
        controller_fields.append(f"    private final {service_name} {service_var};")
        ctor_args.append(f"        {service_name} {service_var}")
        ctor_assigns.append(f"        this.{service_var} = {service_var};")
        method_lines: List[str] = []
        method_doc = render_javadoc_block(str(action.get("description", "")) or None, indent="    ").rstrip("\n")
        if method_doc:
            method_lines.append(method_doc)
        method_lines.extend(
            [
                f"    @PostMapping(\"/{action['name']}\")",
                f"    public ResponseEntity<{res_name}> {method_name}(@Valid @RequestBody {req_name} request) {{",
                "        try {",
                f"            return ResponseEntity.ok({service_var}.execute(request));",
                "        } catch (UnsupportedOperationException ex) {",
                "            throw new ResponseStatusException(NOT_IMPLEMENTED, ex.getMessage(), ex);",
                "        }",
                "    }",
                "",
            ]
        )
        controller_methods.extend(method_lines)

    ctor_signature = ",\n".join(ctor_args)
    action_controller_src = (
        f"package {base_package}.generated.api;\n\n"
        + "\n".join(sorted(controller_imports))
        + "\n\n"
        + "@RestController\n"
        + "@RequestMapping(\"/actions\")\n"
        + "public class ActionEndpointController {\n\n"
        + ("\n".join(controller_fields) + "\n\n" if controller_fields else "")
        + "    public ActionEndpointController(\n"
        + (ctor_signature + "\n" if ctor_signature else "")
        + "    ) {\n"
        + ("\n".join(ctor_assigns) + "\n" if ctor_assigns else "")
        + "    }\n\n"
        + "\n".join(controller_methods)
        + "}\n"
    )
    files[f"src/main/java/{package_path}/generated/api/ActionEndpointController.java"] = action_controller_src
