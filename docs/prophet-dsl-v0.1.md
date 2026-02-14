# Prophet DSL v0.1

This document describes the DSL currently implemented by `prophet-cli`.

## 1. File Structure

Each `.prophet` file defines one ontology:

```prophet
ontology <OntologyName> {
  id "<ontology_id>"
  version "<semver>"
  # blocks...
}
```

Supported top-level blocks:
- `type`
- `object`
- `struct`
- `actionInput` (preferred)
- `actionOutput` (preferred)
- `action`
- `event`
- `trigger`

Compatibility aliases also supported:
- `action_input`
- `action_output`

## 2. Lexical Rules

- Identifier names: `[A-Za-z_][A-Za-z0-9_]*`
- Strings use double quotes: `"..."`
- Empty lines ignored
- `#` line comments supported

## 3. Grammar (Implemented)

```text
ontology      := "ontology" NAME "{" ontology_body "}"
ontology_body := id_line version_line top_block*

id_line       := "id" STRING
version_line  := "version" STRING

top_block     := type_block
               | object_block
               | struct_block
               | action_input_block
               | action_output_block
               | action_block
               | event_block
               | trigger_block

type_block    := "type" NAME "{" type_body "}"
type_body     := id_line base_line constraint_line*
base_line     := "base" BASE_TYPE
constraint_line := "constraint" NAME STRING

object_block  := "object" NAME "{" object_body "}"
object_body   := id_line (field_block | state_block | transition_block)*

struct_block  := "struct" NAME "{" struct_body "}"
struct_body   := id_line field_block*

action_input_block  := ("actionInput" | "action_input") NAME "{" action_shape_body "}"
action_output_block := ("actionOutput" | "action_output") NAME "{" action_shape_body "}"
action_shape_body   := id_line field_block*

field_block   := "field" NAME "{" field_body "}"
field_body    := id_line type_line required_line key_line?
type_line     := "type" type_expr
type_expr     := scalar_type | list_type
list_type     := type_expr "[]" | "list(" type_expr ")"
scalar_type   := BASE_TYPE | NAME | "ref(" NAME ")"
required_line := "required" | "optional"
key_line      := "key" "primary"

state_block   := "state" NAME "{" state_body "}"
state_body    := id_line initial_line?
initial_line  := "initial"

transition_block := "transition" NAME "{" transition_body "}"
transition_body  := id_line from_line to_line
from_line        := "from" NAME
to_line          := "to" NAME

action_block  := "action" NAME "{" action_body "}"
action_body   := id_line kind_line input_line output_line
kind_line     := "kind" ("process" | "workflow")
input_line    := "input" NAME         # actionInput/action_input name
output_line   := "output" NAME        # actionOutput/action_output name

event_block   := "event" NAME "{" event_body "}"
event_body    := id_line kind_event_line object_line action_line? from_line? to_line?
kind_event_line := "kind" ("action_output" | "signal" | "transition")
object_line   := "object" NAME
action_line   := "action" NAME

trigger_block := "trigger" NAME "{" trigger_body "}"
trigger_body  := id_line when_line invoke_line
when_line     := "when" "event" NAME
invoke_line   := "invoke" NAME

BASE_TYPE     := string | int | long | short | byte | double | float | decimal | boolean | datetime | date | duration
```

## 4. Validation Rules

`prophet validate` enforces:

- All entities must define `id`; IDs are globally unique.
- `type.base` must be supported base type.
- `object` fields must use known base/custom/ref types.
- Each `object` must define exactly one `key primary` field.
- Stateful `object` definitions must define exactly one `initial` state.
- `object` transitions must reference valid object states.
- `struct` fields must use known base/custom/ref/struct types and must not declare `key`.
- `actionInput`/`actionOutput` fields must use known base/custom/ref/struct types.
- `actionInput`/`actionOutput` fields must not declare `key`.
- `action.kind` must be `process` or `workflow`.
- `action.input` must reference an existing action input shape.
- `action.output` must reference an existing action output shape.
- Event kind must be one of `action_output`, `signal`, `transition`.
- Event object must exist.
- `action_output` events must reference an existing action.
- `transition` events must provide valid `from`/`to` states for the event object.
- Trigger event/action references must exist.

## 5. Action Contract Model

Actions now use explicit input/output contracts:

- `actionInput` defines request payload shape.
- `actionOutput` defines response payload shape.
- Generated Spring action endpoints consume/return these contracts at `POST /actions/<actionName>`.
- Action execution logic is not auto-generated; handlers are user-implemented.
- Generated default handler stubs throw `UnsupportedOperationException` until user handlers are present.

## 6. Ref Semantics

- `ref(ObjectName)` is an object reference, not an inline struct.
- In OpenAPI/domain contracts, refs map to `<ObjectName>Ref` payloads.
- For object persistence, scalar `ref(...)` maps to JPA `@ManyToOne`.
- For list refs (`ref(User)[]` / `list(ref(User))`), values are stored as JSON in a generated converter-backed column.

## 7. Field Order Semantics

- Field declaration order is preserved in generated Java record component order.
- This applies to object records, structs, `actionInput`, and `actionOutput` records.
- Reordering fields in DSL can require corresponding constructor argument order updates in user code.

## 8. Full Example

See:
- `ontology/local/main.prophet`

This file is the source of truth for the current supported syntax.

## 9. Current Limitations (v0.1)

- Cross-file imports/namespaces are not yet supported.
- Advanced trigger filter expressions are not yet supported.

## 10. Generation Targets (Config)

Typical `prophet.yaml` target configuration:

```yaml
generation:
  targets:
    - sql
    - openapi
    - spring_boot
    - flyway
    - liquibase
```

Target outputs:
- `sql` -> `gen/sql/schema.sql`
- `openapi` -> `gen/openapi/openapi.yaml`
- `spring_boot` -> `gen/spring-boot/**`
- `flyway` -> `gen/migrations/flyway/V1__prophet_init.sql`
- `liquibase` -> `gen/migrations/liquibase/**`
