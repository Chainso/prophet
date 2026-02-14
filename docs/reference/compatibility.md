# Compatibility Reference

This policy is used by:
- `prophet plan`
- `prophet version check`
- `prophet check`

## Classification Levels

| Level | Required bump | Meaning |
|---|---|---|
| `breaking` | `major` | Existing consumers may fail without coordinated changes |
| `additive` | `minor` | Backward-compatible expansion |
| `non_functional` | `patch` | No wire/data contract impact |

## Field Rules

| Change | Classification |
|---|---|
| Field removed | `breaking` |
| Required field added (`min > 0`) | `breaking` |
| Optional field added (`min = 0`) | `additive` |
| Incompatible type change | `breaking` |
| Type widening | `additive` |
| Cardinality min increase | `breaking` |
| Cardinality min decrease | `additive` |
| Cardinality max decrease | `breaking` |
| Cardinality max increase | `additive` |
| Field reorder | `non_functional` |

## Object/State Rules

| Change | Classification |
|---|---|
| Object removed | `breaking` |
| Object added | `additive` |
| State removed | `breaking` |
| State added | `additive` |
| Transition removed | `breaking` |
| Transition added | `additive` |

## Type Rules

| Change | Classification |
|---|---|
| Type removed | `breaking` |
| Type added | `additive` |
| Type base changed incompatibly | `breaking` |
| Type constraints changed | `breaking` |

## Action/Event/Trigger Rules

| Change | Classification |
|---|---|
| Definition removed | `breaking` |
| Definition added | `additive` |
| Definition modified | `breaking` |

## Query Contract Rules

| Change | Classification |
|---|---|
| Query contract removed | `breaking` |
| Query contract added | `additive` |
| Query path changed | `breaking` |
| Query filter removed | `breaking` |
| Query filter added | `additive` |
| Query operator removed | `breaking` |
| Query operator added | `additive` |

## Migration Safety Flags

Delta migrations include safety flags:
- `destructive_changes=true`
- `backfill_required=true`
- `manual_review_required=true`
