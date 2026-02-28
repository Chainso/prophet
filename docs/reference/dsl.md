# DSL Reference

## Top-Level Structure

```prophet
ontology CommerceLocal {
  name "Commerce Local"
  version "0.1.0"
  # type/object/struct/action/signal/trigger blocks
}
```

## Supported Top-Level Blocks

- `type`
- `object`
- `struct`
- `action`
- `signal`
- `trigger`

## Lexical Rules

- Identifier names: `[A-Za-z_][A-Za-z0-9_]*`
- Strings use double quotes
- `#` starts a line comment
- Empty lines are ignored

## Technical Symbol vs Display Name

- The block identifier is the technical symbol (`object Order`, `field order_id`, etc.).
- Optional metadata `name "..."` is the human-facing display name.
- If `name` is omitted, display name defaults to the technical symbol.
- References and generated wire keys still use technical symbols.

## IDs

- `id "..."` is optional on ontology elements.
- When omitted, Prophet generates a stable non-conflicting ID during parse.
- CLI commands that parse the ontology (`validate`, `plan`, `gen`, `check`) materialize missing IDs back into the source `.prophet` file immediately.
- You can still provide explicit IDs anywhere you need stable external references.

## Field Types

Supported field type forms:
- Base scalars: `string`, `int`, `long`, `short`, `byte`, `double`, `float`, `decimal`, `boolean`, `datetime`, `date`, `duration`
- Custom types: `<TypeName>`
- Object references: `ref(User)`
- Lists: `string[]`, `list(string)`
- Nested lists: `string[][]`, `list(list(string))`
- Structs: `<StructName>`

## Keys

Primary key declarations:
- Field-level: `key primary`
- Object-level single/composite: `key primary (fieldA, fieldB)`

Display key declarations:
- Field-level: `key display`
- Object-level single/composite: `key display (fieldA, fieldB)`

Display key generation behavior:
- SQL/Flyway/Liquibase generators emit a non-unique display index when `key display` is explicitly declared and differs from the primary key columns.
- Node Prisma and Mongoose generators also emit non-unique display indexes from `key display`.

## Metadata

Supported metadata lines on ontology elements and fields:

- `name "..."` for human-facing display names
- `description "..."` for short descriptive text
- `documentation "..."` as a synonym for `description`

Example:

```prophet
field customer_id {
  name "Customer ID"
  type string
  description "Stable customer identifier."
}
```

## Field Requiredness

- Fields are `required` by default.
- Use `optional` only when a field should be nullable/omittable.
- `required` remains supported as an explicit marker.

## Action Contracts

Actions declare command contracts inline with `input { ... }`.
Action output is an event, and can be declared in three forms.

```prophet
action createOrder {
  kind process

  input {
    field customer_id {
      type string
    }
  }

  output signal PaymentCaptured
}
```

Supported output forms:
- Inline signal payload:
  - `output { ... }`
  - derives signal event `<ActionName> Result`
- Referenced signal:
  - `output signal <SignalName>`
- Referenced transition:
  - `output transition <ObjectName>.<TransitionName>`

## Event Semantics

- Top-level event definitions in DSL are `signal` declarations.
- Object `transition` declarations are also events.
- Action output always resolves to an event (`signal` or `transition`).
- Triggers can reference:
  - signal name (for example `PaymentCaptured`)
  - derived inline output signal name `<ActionName> Result` (for example `ApproveOrder Result`)
  - derived transition event name `<Object><Transition>Transition` (for example `OrderApproveTransition`)
- Action input shape names are derived as `<ActionName> Command` (for example `ApproveOrder Command`).
- If an action defines display metadata (`name "..."`), derived inline names use that display value as the `<ActionName>` base.
- Transition events automatically include object primary key fields, `fromState`, and `toState`.

Signal example:

```prophet
signal PaymentCaptured {
  field orderId {
    type string
  }
}
```

## Validation Highlights

`prophet validate` enforces:
- unique IDs across definitions
- valid state/transition references
- key constraints
- action/event/trigger link integrity
- object-ref target constraints (currently single-field PK targets)
- valid action input and output-event wiring in action definitions
- signal schema validity
- valid trigger references to existing events/actions
- reserved field name `state` cannot be user-defined

## Canonical Example

- [examples/java/prophet_example_spring/ontology/local/main.prophet](../../examples/java/prophet_example_spring/ontology/local/main.prophet)
- [examples/turtle/prophet_example_turtle_small_business/ontology/local/main.prophet](../../examples/turtle/prophet_example_turtle_small_business/ontology/local/main.prophet)

## Current Limitations

- Cross-file imports and namespaces are not yet supported.
- Advanced trigger filter expressions are not yet supported.
