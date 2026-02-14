# Prophet Spec v0.1

## 1. Purpose

Prophet is the ontology compiler kernel for Seer.  
In v0.1, Prophet focuses on local ontology authoring, validation, deterministic planning, and generation.

## 2. Scope (v0.1)

Included:
- Local ontology DSL
- Parser -> canonical IR
- Validation (structural + semantic)
- Compatibility classification (`breaking`, `additive`, `non_functional`)
- Deterministic artifact generation
- Golden stack generator for Spring Boot
- Deterministic Flyway + Liquibase migration artifact generation
- Minimal CLI (`init`, `validate`, `plan`, `generate`, `version check`)

Not included:
- Data migration engine
- Multi-version runtime orchestration
- Plugin marketplace
- UI/editor features beyond file-based workflow

## 3. Core Contracts

### 3.1 Identity

- Every ontology entity has an immutable `id`.
- `id` is the source of truth for references (not display name).
- Display metadata (`name`, `description`, `documentation`) is mutable.
- Deleted IDs must not be reused.

Entity types requiring immutable IDs:
- `object_model`
- `field`
- `state`
- `transition`
- `action`
- `event`
- `trigger`
- `custom_type`
- `enum_value`

### 3.2 Compatibility Principle

A change is **breaking** if any previously valid payload, transition, query contract, or dispatch behavior becomes invalid or differently interpreted.

### 3.3 Determinism

- Same input DSL + same toolchain version => byte-identical IR, plan output, and generated artifacts.
- No timestamps, random ordering, or machine-specific absolute paths in outputs.
- Canonical ordering is required for entities and fields.

## 4. Change Classification Matrix (v0.1)

Legend:
- `B` = Breaking
- `A` = Additive
- `N` = Non-functional

| Change | Class | Notes |
|---|---|---|
| Rename `name`/`description`/docs only | N | IDs unchanged |
| Change/remove entity `id` | B | Contract identity break |
| Add optional field | A | No existing payload invalidated |
| Add required field | B | Existing payloads may fail validation |
| Remove field | B | Existing readers/writers can break |
| Scalar type narrowing (`string`->`uuid`, `i64`->`i32`) | B | Potential invalidation/truncation |
| Scalar type widening (`i32`->`i64`) | A* | `B` if any target loses fidelity |
| Enum value add | A | Treat as `B` for strict closed-world consumers |
| Enum value remove/rename | B | Existing values become invalid |
| Cardinality tighten (`min 0->1`, `max 10->5`) | B | Invalidates existing data |
| Cardinality loosen (`min 1->0`, `max 1->n`) | A* | `B` if wire shape changes scalar<->list |
| List <-> scalar shape change | B | Generated API/types contract break |
| Nested list depth change (`T[]` -> `T[][]`) | B | Wire/API shape change |
| Struct field add (optional) | A | Existing payloads remain valid |
| Struct field add (required) | B | Existing payloads can fail validation |
| Struct field remove | B | Existing payload readers/writers can break |
| Struct field type/cardinality tighten | B | Contract invalidation |
| Custom type constraint change | B | Conservatively treated as contract-tightening |
| Add state | A | Usually safe |
| Remove state | B | Existing instances/transitions invalid |
| Add transition | A* | `B` if it changes trigger/action behavior for existing flows |
| Remove transition | B | Existing flow paths invalid |
| Change trigger predicate | B | Behavioral contract change |
| Change trigger target action | B | Behavioral contract change |
| Add new event type/action | A | No removal/rewire |
| Remove event/action | B | Existing producers/consumers break |

## 5. Versioning Policy

- Ontology has explicit `version` (semver).
- Compatibility result drives required version bump:
- `breaking` -> `major`
- `additive` -> `minor`
- `non_functional` -> `patch`

CI policy:
- If computed required bump > declared bump, fail.
- If declared bump is larger than required, allow.

## 6. DSL v0.1 Surface

Required modeling constructs:
- Object models with fields
- Types (base, enum/custom, object reference)
- States and transitions
- Actions (`process`, `workflow`)
- Events (`action_output`, `signal`, `transition`)
- Triggers (event -> action mapping, optional filter)

Minimum required per field:
- `id`
- `name`
- `type`
- cardinality (`required` or `{min,max}`)

## 7. Canonical IR (Compiler Boundary)

Pipeline:
1. Parse DSL
2. Resolve references by `id`
3. Normalize defaults
4. Canonical sort
5. Emit IR JSON (stable schema + hash)

IR principles:
- Lossless with respect to DSL semantics
- Explicit default expansion
- Suitable as single input to validator and generators

## 8. CLI v0.1 UX

### 8.1 `prophet init`

Creates starter project layout and sample ontology.

Example:
```bash
prophet init
```

Example output:
```text
Initialized Prophet project.
Created:
- prophet.yaml
- ontology/local/main.prophet
- .prophet/ir
- .prophet/baselines

Note: gen/ is created on first 'prophet gen' or 'prophet generate'.
```

### 8.2 `prophet validate`

Validates syntax and ontology semantics.

Example:
```bash
prophet validate
```

Example output:
```text
Validation failed (2 errors):
1) ontology/local/main.prophet:42:5 field `total_amount` cardinality min=1 conflicts with default=null
2) ontology/local/main.prophet:87:3 transition `order_ship` references unknown state id `state_order_shipped`
```

### 8.3 `prophet plan`

Shows deterministic diff of affected artifacts and why.

Example:
```bash
prophet plan
```

Example output:
```text
Plan: 3 changes
1) gen/sql/schema.sql (modified)
   reason: field added `order.discount_code` (optional string)
2) gen/openapi/openapi.yaml (modified)
   reason: object `Order` response schema changed
3) gen/spring-boot/src/main/java/com/example/prophet/generated/domain/Order.java (modified)
   reason: generated model `Order` gained nullable property `discountCode`

Compatibility: additive
Required version bump: minor
```

### 8.4 `prophet generate`

Writes generated artifacts from canonical IR.

Example:
```bash
prophet generate
```

Example output:
```text
Generated artifacts:
- gen/sql/schema.sql
- gen/migrations/flyway/V1__prophet_init.sql
- gen/migrations/liquibase/db.changelog-master.yaml
- gen/openapi/openapi.yaml
- gen/spring-boot/build.gradle.kts
- gen/spring-boot/src/main/java/com/example/prophet/generated/domain/Order.java
- gen/spring-boot/src/main/java/com/example/prophet/generated/api/ActionEndpointController.java
```

### 8.5 `prophet version check`

Compares current ontology against a baseline snapshot and reports compatibility.

Example:
```bash
prophet version check --against .prophet/baselines/main.ir.json
```

Example output:
```text
Compatibility result: breaking
Required version bump: major

Detected breaking changes:
- field removed: object=order field_id=field_order_total
- cardinality tightened: object=invoice field_id=field_due_date min 0 -> 1
```

## 9. Project Layout (v0.1)

```text
.
├── prophet.yaml
├── ontology/
│   └── local/
│       └── main.prophet
├── .prophet/
│   ├── ir/
│   │   └── current.ir.json
│   └── baselines/
│       └── main.ir.json
└── gen/
    ├── migrations/
    │   ├── flyway/
    │   └── liquibase/
    ├── sql/
    ├── openapi/
    └── spring-boot/
```

Rules:
- `gen/` is tool-owned (no manual edits).
- User logic lives outside `gen/`.

## 10. CI Gates (v0.1)

Required CI steps:
1. `prophet validate`
2. `prophet version check --against <baseline>`
3. `prophet generate --verify-clean`

`--verify-clean` fails if regenerated output differs from committed artifacts.

## 11. MVP Done Criteria

MVP is done when:
1. Engineers can model local ontology in DSL.
2. Validation catches semantic errors with source locations.
3. `plan` reports deterministic file-level changes with reasons.
4. `generate` outputs DB/API/types for one golden stack.
5. CI blocks incompatible changes unless declared version bump is sufficient.

## 12. Golden Stack: Spring Boot (v0.1)

The v0.1 golden stack is:
- PostgreSQL for relational persistence
- OpenAPI for HTTP contract
- Spring Boot 3.x (Java 21) for server runtime integration

Minimum generated Spring integration surface:
- Domain model classes (from object models and types)
- State/transition guard helpers
- Action endpoint controllers (one endpoint per action under `/actions/*`)
- Default action handler stubs (throwing unsupported operation until overridden)
- Repository interfaces for generated entities
- Paginated/filterable query controllers (`GET /<objects>` + `GET /<objects>/{id}`)
- Configuration properties for generated API behavior
- Deterministic JPA mappings (tables, columns, FK relations, optimistic locking, state history)
- Generated Flyway and Liquibase resources in Spring module (`src/main/resources/db/**`)

Generation boundary:
- `gen/spring-boot/.../generated` is tool-owned
- User implementations live outside generated packages (for example `.../app` or `.../extensions`)
- Regeneration must not modify user-owned files

Detailed mapping reference:
- `docs/prophet-jpa-mapping-v0.1.md`
