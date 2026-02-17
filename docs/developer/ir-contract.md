# IR Contract

## Purpose

IR is the stable internal contract between DSL/validation and target generators.

## Core Invariants

- Canonical ordering for deterministic generation
- Explicit IDs for compatibility classification
- Query contracts captured as versioned IR surface (`query_contracts`, `query_contracts_version`)
- Action contracts represented through declared input shape + produced event references (`input_shape_id`, `output_event_id`)
- Event kinds are `signal` or `transition` only (no `action_output` kind)
- Transition event payloads include implicit object PK fields plus `fromState` and `toState`

## Consumer Boundary

Generators should consume IR through typed reader interfaces where possible (`IRReader`) rather than ad hoc dict traversal.

## Compatibility Link

Compatibility logic compares baseline IR and current IR to determine required semantic version bump.
