# IR Contract

## Purpose

IR is the stable internal contract between DSL/validation and target generators.

## Core Invariants

- Canonical ordering for deterministic generation
- Explicit IDs for compatibility classification
- Query contracts captured as versioned IR surface (`query_contracts`, `query_contracts_version`)
- Action contracts represented through declared input/output shape references

## Consumer Boundary

Generators should consume IR through typed reader interfaces where possible (`IRReader`) rather than ad hoc dict traversal.

## Compatibility Link

Compatibility logic compares baseline IR and current IR to determine required semantic version bump.
