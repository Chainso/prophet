---
name: prophet-execute-ontology-change
description: Execute Prophet ontology changes directly by editing DSL source files, validating, planning, regenerating artifacts, and verifying integration outcomes. Use when users ask to add, change, or refactor domain models, actions, events, triggers, refs, structs, enums, keys, state fields, or query behavior.
license: See LICENSE for complete terms
allowed-tools: Bash(prophet:validate:*) Bash(prophet:plan:*) Bash(prophet:check:*) Bash(prophet:stacks:*) Bash(prophet:hooks:*) Bash(prophet:version:check:*) Bash(prophet:generate:--verify-clean:*) Bash(prophet:gen:--verify-clean:*)
---

# Prophet Execute Ontology Change

## Operator Contract

- Perform the work directly. Do not stop at recommendations.
- Only pause for: missing required business decisions, permission blocks, or destructive ambiguity.
- Edit source-of-truth files (`.prophet`, `prophet.yaml`, user-owned code), not generated `gen/**` as the primary fix path.

## Inputs to Resolve

1. Locate Prophet project root (`prophet.yaml`).
2. Resolve ontology DSL path from `project.ontology_file`.
3. Infer active stack and targets from `generation.stack` and `generation.targets`.

## Canonical Ontology Example

Use this real example as your baseline when authoring or refactoring ontology DSL:
- `examples/java/prophet_example_spring/ontology/local/main.prophet`

Representative excerpt (covers type/object/enum/struct/action/event/trigger/state-field):

```prophet
ontology commerce_local {
  id "ont_commerce_local"
  version "1.0.0"

  type Money {
    id "type_money"
    base decimal
    constraint min "0.00"
  }

  enum OrderStatus {
    id "enum_order_status"

    value Created {
      id "enum_order_status_created"
    }

    value Approved {
      id "enum_order_status_approved"
    }
  }

  object Order {
    id "obj_order"

    field order_id {
      id "fld_order_order_id"
      type string
      key primary
    }

    field customer {
      id "fld_order_customer"
      type ref(User)
    }

    field discount_code {
      id "fld_order_discount_code"
      type string
      optional
    }

    field status {
      id "fld_order_status"
      type OrderStatus
      state
      initial Created
    }
  }

  struct ApprovalContext {
    id "struct_approval_context"

    field approver {
      id "fld_struct_approval_context_approver"
      type ref(User)
    }
  }

  action approveOrder {
    id "act_approve_order"

    input {
      id "ain_approve_order"
      field order {
        id "fld_ain_approve_order_order"
        type ref(Order)
      }
    }

    output {
      id "aout_approve_order"
      field decision {
        id "fld_aout_approve_order_decision"
        type string
      }
    }
  }

  event PaymentCaptured {
    id "evt_payment_captured"
    field order {
      id "fld_evt_payment_captured_order"
      type ref(Order)
    }
  }

  trigger onPaymentCaptured {
    id "trg_on_payment_captured"
    when event PaymentCaptured
    invoke approveOrder
  }
}
```

## Ontology Concepts Rundown

Use this as the default decision guide when applying ontology changes.

1. `ontology <Name> { ... }`
   - Root contract for one bounded domain model.
   - Owns versioning and all top-level definitions.
   - Keep `id` stable once published; treat as compatibility anchor.

2. `id "..."` (on ontology elements)
   - Stable identity across refactors and renames.
   - Never recycle old IDs for new concepts.
   - Prefer add-new IDs instead of mutating semantic meaning of existing IDs.

3. `version "x.y.z"` (ontology)
   - Declared semantic version for compatibility policy checks.
   - Must align with compatibility impact (`breaking`/`additive`/`non-functional`).

4. `type <TypeName> { base ... constraint ... }`
   - Reusable scalar alias with constraints.
   - Use for domain primitives (`Money`, `Email`, `Sku`) reused across many fields.

5. `object <ObjectName> { ... }`
   - Persistent domain entity/aggregate that generates storage and query surfaces.
   - Owns fields, keys, and optional enum-backed state metadata on one field.

6. `field <fieldName> { type ... }`
   - Atomic schema unit used in objects, structs, action input/output, and events.
   - Fields are required by default; use `optional` only when null/omission is intended.
   - Supported type forms:
     - scalars: `string`, `int`, `long`, `short`, `byte`, `double`, `float`, `decimal`, `boolean`, `datetime`, `date`, `duration`
     - custom type: `Money`
     - enum: `OrderStatus`
     - object ref: `ref(User)`
     - struct: `Address`
     - lists: `string[]`, `list(string)`, nested lists such as `string[][]`

7. Keys
   - Field-level primary key: `key primary` in a field block.
   - Object-level key declarations are supported (single/composite, display-key metadata).
   - Use primary keys only for stable identity fields.

8. `struct <StructName> { ... }`
   - Embedded reusable value object; not a top-level persistent aggregate.
   - Use when the shape is reused and does not need independent lifecycle/query identity.

9. `enum <EnumName> { value ... }`
   - Declares reusable enumerated values for fields and state modeling.
   - Use top-level enums for workflow/status concepts that appear in multiple contracts.

10. State fields on objects
   - Mark exactly one object field with `state` to identify lifecycle state.
   - The field must reference an enum and declare `initial <EnumValue>`.
   - State is ordinary persisted/queryable field data; there is no separate workflow graph syntax.

11. `action <ActionName> { input { ... } output { ... } }`
   - Command API boundary generated as action endpoint + contracts.
   - Keep action contracts explicit and stable; evolve additively when possible.

12. Action `input` / `output` blocks
   - Define request/response payload contracts inline.
   - These contracts drive generated DTOs/schemas and event contracts.
   - Supported output forms:
     - inline event payload: `output { ... }`
     - declared top-level event: `output event <EventName>`

13. `event <EventName> { ... }`
   - Explicit top-level domain event declaration.
   - Use for external or system events that should trigger actions, or for reusable action output payloads.

14. `trigger <TriggerName> { when event ... invoke ... }`
   - Event-to-action automation rule.
   - `when event` references a declared event name or an inline action-output-derived event name.

15. Derived event model (important)
   - Top-level events are explicit.
   - Inline action outputs derive event contracts such as `<ActionName> Result`.
   - There is no secondary signal/transition event subtype.

16. Description metadata
   - `description "..."` and `documentation "..."` are supported synonyms.
   - Use for developer clarity; do not rely on description text for identity semantics.

17. Query behavior model
   - `object` definitions generate query/read surfaces:
     - by-id fetch,
     - list pagination/sort,
     - typed filter query endpoint.
   - Query capabilities come from object field contracts and types; no separate query DSL block is required.

## Execution Workflow

1. Read current ontology and identify impacted concepts.
2. Apply DSL edits to satisfy user intent.
3. Preserve current Prophet modeling rules:
   - fields are required by default; use `optional` when needed,
   - actions use inline `input {}` and an event output form: `output {}` or `output event <EventName>`,
   - use `ref(ObjectName)` for object references,
   - use `struct` for embedded value objects,
   - use top-level `event` blocks for declared events,
   - use enum-backed object fields marked `state` with `initial <EnumValue>` for lifecycle state.
4. Run validation:
   - `prophet validate`
5. Run compatibility/impact plan:
   - `prophet plan --show-reasons`
6. Regenerate:
   - `prophet gen`
   - use `prophet gen --wire-gradle` when Java Spring module wiring is expected.
7. Run project verification gates when available:
   - Java: `./gradlew test`
   - Node: `npm run build` and `npm run test:integration` if present
   - Python: framework test suite (`pytest` if configured)
8. If failures occur, fix root causes and repeat validate/plan/gen/test loop.

## Completion Criteria

- Ontology intent is implemented in DSL.
- `prophet validate` passes.
- Regeneration completed without unresolved errors.
- Relevant project tests/build checks pass or clearly documented if blocked.

## Response Requirements

- Summarize exact files changed.
- Include key command outcomes.
- Call out any follow-up required from the user only if truly necessary.
