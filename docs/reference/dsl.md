# DSL Reference

## Top-Level Structure

```prophet
ontology CommerceLocal {
  id "ontology_commerce_local"
  version "0.1.0"
  # type/object/struct/actionInput/actionOutput/action/event/trigger blocks
}
```

## Supported Top-Level Blocks

- `type`
- `object`
- `struct`
- `actionInput` / `action_input`
- `actionOutput` / `action_output`
- `action`
- `event`
- `trigger`

## Lexical Rules

- Identifier names: `[A-Za-z_][A-Za-z0-9_]*`
- Strings use double quotes
- `#` starts a line comment
- Empty lines are ignored

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

Display key metadata marker:
- `key display (...)`

## Description Metadata

`description "..."` and `documentation "..."` are supported synonyms.

## Action Contracts

Actions must point to explicit input/output shapes:

```prophet
actionInput CreateOrderCommand {
  id "shape_create_order_cmd"
  field customer_id {
    id "fld_create_order_customer_id"
    type string
    required
  }
}

actionOutput CreateOrderResult {
  id "shape_create_order_result"
  field order_id {
    id "fld_create_order_result_order_id"
    type string
    required
  }
}

action createOrder {
  id "act_create_order"
  kind process
  input CreateOrderCommand
  output CreateOrderResult
}
```

## Validation Highlights

`prophet validate` enforces:
- unique IDs across definitions
- valid state/transition references
- key constraints
- action/event/trigger link integrity
- object-ref target constraints (currently single-field PK targets)
- valid `actionInput`/`actionOutput` references in action definitions
- valid event kind semantics (`action_output`, `signal`, `transition`)
- valid trigger references to existing events/actions

## Canonical Example

- [examples/java/prophet_example_spring/ontology/local/main.prophet](../../examples/java/prophet_example_spring/ontology/local/main.prophet)

## Current Limitations

- Cross-file imports and namespaces are not yet supported.
- Advanced trigger filter expressions are not yet supported.
