# Prophet Compatibility Policy v0.2

This document defines the semantic compatibility contract used by `prophet plan`, `prophet version check`, and `prophet check`.

## Classification Levels

| Level | Required SemVer Bump | Meaning |
|---|---|---|
| `breaking` | `major` | Existing consumers may fail without coordinated changes or data migration |
| `additive` | `minor` | Backward-compatible expansion |
| `non_functional` | `patch` | No wire/data contract impact |

## Field Rules

| Change | Classification | Notes |
|---|---|---|
| Field removed | `breaking` | Consumer contract removed |
| Required field added (`min > 0`) | `breaking` | Existing payloads/data may be invalid |
| Optional field added (`min = 0`) | `additive` | Backward-compatible addition |
| Type changed incompatibly | `breaking` | Includes scalar/list shape changes |
| Type widened | `additive` | Supported widening paths only |
| Cardinality min increased | `breaking` | Stricter requirement |
| Cardinality min decreased | `additive` | Looser requirement |
| Cardinality max decreased | `breaking` | Stricter bound |
| Cardinality max increased | `additive` | Looser bound |
| Field order changed | `non_functional` | IDs are compatibility anchors; order is not schema-breaking |

## Object/State Rules

| Change | Classification | Notes |
|---|---|---|
| Object removed | `breaking` | Contract deleted |
| Object added | `additive` | New capability |
| State removed | `breaking` | Lifecycle contract removed |
| State added | `additive` | Lifecycle extension |
| Transition removed | `breaking` | Existing flows may fail |
| Transition added | `additive` | New lifecycle path |

## Type Rules

| Change | Classification | Notes |
|---|---|---|
| Type removed | `breaking` | Referenced contracts may fail |
| Type added | `additive` | New reusable type |
| Type base changed incompatibly | `breaking` | Wire/storage incompatibility |
| Type constraints changed | `breaking` | Existing values may become invalid |

## Action/Event/Trigger Rules

| Change | Classification | Notes |
|---|---|---|
| Definition removed | `breaking` | Invocation/dispatch path removed |
| Definition added | `additive` | New capability |
| Definition modified | `breaking` | Treated as behavior contract change |

## Migration Safety Flags

Delta migrations include flags in generated SQL:

| Flag | Meaning |
|---|---|
| `destructive_changes=true` | Potential destructive operations detected (manual review required) |
| `backfill_required=true` | Data backfill needed before enforcing stricter constraints |
| `manual_review_required=true` | Human validation required before production rollout |
