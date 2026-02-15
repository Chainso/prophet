# DSL Reference

## Top-Level Structure

```prophet
ontology CommerceLocal {
  id "ontology_commerce_local"
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
- `actionInput` / `action_input` (explicit reusable contract blocks)
- `actionOutput` / `action_output` (explicit reusable contract blocks)

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

Actions can declare contracts inline (recommended) or reference named top-level shapes.

```prophet
action createOrder {
  id "act_create_order"
  kind process

  input CreateOrderCommand {
    id "shape_create_order_cmd"
    field customer_id {
      id "fld_create_order_customer_id"
      type string
      required
    }
  }

  output CreateOrderResult {
    id "shape_create_order_result"
    field order_id {
      id "fld_create_order_result_order_id"
      type string
      required
    }
  }
}
```

## Event Semantics

- `signal` is the only explicit top-level event definition in the DSL.
- `actionOutput` contracts are event types by definition and are derived automatically as events.
- object `transition` definitions are also derived automatically as events.
- triggers can reference any derived event name:
  - signal name (for example `PaymentCaptured`)
  - action output shape name (for example `ApproveOrderResult`)
  - derived transition event name `<Object><Transition>Transition` (for example `OrderApproveTransition`)

Signal example:

```prophet
signal PaymentCaptured {
  id "sig_payment_captured"
  field orderId {
    id "fld_sig_payment_captured_order_id"
    type string
    required
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
- valid action input/output references in action definitions
- signal schema validity
- valid trigger references to existing events/actions

## Canonical Example

- [examples/java/prophet_example_spring/ontology/local/main.prophet](../../examples/java/prophet_example_spring/ontology/local/main.prophet)

## Current Limitations

- Cross-file imports and namespaces are not yet supported.
- Advanced trigger filter expressions are not yet supported.
