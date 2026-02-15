from __future__ import annotations

from typing import Any, Dict

from ..support import _camel_case
from ..support import _pascal_case

def _render_action_service(ir: Dict[str, Any]) -> str:
    action_input_by_id = {item["id"]: item for item in ir.get("action_inputs", []) if isinstance(item, dict) and "id" in item}
    action_output_by_id = {item["id"]: item for item in ir.get("action_outputs", []) if isinstance(item, dict) and "id" in item}

    lines: List[str] = [
        "// GENERATED FILE: do not edit directly.",
        "",
        "import type * as Actions from './actions';",
        "import type { GeneratedActionContext, GeneratedActionHandlers } from './action-handlers';",
        "import type { GeneratedEventEmitter } from './events';",
        "",
        "export class GeneratedActionExecutionService {",
        "  constructor(",
        "    private readonly handlers: GeneratedActionHandlers,",
        "    private readonly eventEmitter: GeneratedEventEmitter,",
        "  ) {}",
        "",
    ]

    for action in sorted(ir.get("actions", []), key=lambda item: str(item.get("id", ""))):
        if not isinstance(action, dict):
            continue
        action_name = str(action.get("name", "action"))
        pascal = _pascal_case(action_name)
        camel = _camel_case(action_name)
        input_name = _pascal_case(str(action_input_by_id.get(str(action.get("input_shape_id", "")), {}).get("name", "Input")))
        output_name = _pascal_case(str(action_output_by_id.get(str(action.get("output_shape_id", "")), {}).get("name", "Output")))

        lines.append(f"  async {camel}(input: Actions.{input_name}, context: GeneratedActionContext): Promise<Actions.{output_name}> {{")
        lines.append(f"    const output = await this.handlers.{camel}.handle(input, context);")
        lines.append(f"    await this.eventEmitter.emit{output_name}(output);")
        lines.append("    return output;")
        lines.append("  }")
        lines.append("")

    lines.append("}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


