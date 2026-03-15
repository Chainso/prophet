# Event And State Model

## Summary

Prophet now models events as a single concept and state as field metadata.

- Top-level event definitions use `event`.
- Actions produce events with either `output event <EventName>` or inline `output { ... }`.
- Object lifecycle state is represented by a normal enum field marked with:
  - `state`
  - `initial <EnumValue>`
- Generators persist and query the declared field name directly.

## DSL Shape

```prophet
enum OrderStatus {
  value Created
  value Approved
}

object Order {
  field orderId {
    type string
    key primary
  }

  field status {
    type OrderStatus
    state
    initial Created
  }
}

event OrderApproved {
  field order {
    type ref(Order)
  }
}

action approveOrder {
  input {
    field order {
      type ref(Order)
    }
  }

  output event OrderApproved
}
```

## Compiler Rules

- Each object may mark at most one field with `state`.
- A state field must use an enum type.
- A state field must declare exactly one `initial <EnumValue>`.
- `initial <EnumValue>` is invalid unless the field is marked `state`.
- There is no object-level workflow-block syntax.
- There is no secondary event subtype.

## IR And Generation

- IR events are uniform event payload definitions with no event kind partition.
- Objects no longer carry `states` or `transitions` collections.
- State metadata lives on the field entry:
  - `is_state_field`
  - `initial_enum_value_id`
- Generators no longer emit:
  - workflow-specific runtime helpers
  - transition draft payloads
  - transition history tables or collections
  - internal synthetic state storage
  - transition validation runtime contracts

## Operational Consequences

- State changes are ordinary writes to a declared enum field.
- Automatic workflow graph enforcement is gone.
- Automatic transition history is gone.
- Consumers that need workflow rules should implement them in user-owned handlers or validators around ordinary field updates.
