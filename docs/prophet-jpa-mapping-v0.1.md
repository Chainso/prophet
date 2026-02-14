# Prophet Ontology -> Spring JPA Mapping v0.1

## 1. Objective

Define a deterministic translation from Prophet ontology constructs to a relational layout and Spring JPA model that is practical for production and stable under regeneration.

## 2. Mapping Strategy

Use a hybrid layout:

1. Typed domain tables per object model
- Best for queryability, constraints, and Spring/JPA ergonomics.

2. Generated ontology catalog tables
- Persist state and transition metadata derived from ontology.
- Enables runtime validation and introspection without parsing ontology source at request time.

3. Per-object transition history tables
- Persist lifecycle transitions for audit and analytics.

This avoids EAV-only storage while preserving ontology semantics.

## 3. Entity Translation Rules

### 3.1 Object Model -> Table + JPA Entity

For each `object_model`:
- Generate table `<object_plural_name>`
- Generate `@Entity` with `@Id` using ontology primary key field
- Add generated technical columns:
  - `row_version bigint not null` (`@Version`)
  - `created_at timestamptz not null`
  - `updated_at timestamptz not null`
  - `current_state text not null` if model has states

### 3.2 Field -> Column

- `required` => `not null`
- optional => nullable
- scalar types map by canonical map (see section 6)
- `custom type` maps to its base SQL type plus generated checks when possible

### 3.3 Object Reference -> Foreign Key

A field of `ref(TargetObject)` maps to:
- FK column `<field_name>_<target_pk_name>`
- `@ManyToOne(fetch = LAZY)` relation in JPA
- `ON UPDATE RESTRICT ON DELETE RESTRICT` by default

### 3.4 Cardinality

- `max=1` => scalar column/relation
- `max>1` or unbounded => JSON-backed `text` column plus generated JPA `AttributeConverter`

List field converter behavior:
- serialize list values as JSON on write
- deserialize JSON back to typed `List<T>` on read
- supports nested list element types (for example `List<List<String>>`)

### 3.5 States and Transitions

For object models with states:
- Persist current state on object row (`current_state`)
- Generate state catalog rows in `prophet_state_catalog`
- Generate transition catalog rows in `prophet_transition_catalog`
- Generate `<object_table>_state_history` table for executed transitions

### 3.6 Actions

Each ontology action generates:
- API endpoint: `POST /actions/<actionName>`
- Request/response DTOs from ontology action contracts
- Action handler interface `<ActionName>ActionHandler`
- Default action handler stub (`@ConditionalOnMissingBean`) that throws `UnsupportedOperationException`

### 3.7 Events in Codegen Scope

In v0.1 Spring codegen:
- Event ingestion is not generated.
- Seer owns ingestion/dispatch orchestration.
- Prophet action endpoints can return data that Seer uses to build platform events.

## 4. Catalog Tables

### 4.1 `prophet_state_catalog`

Purpose:
- Runtime source of truth for model state ids/names.

Columns:
- `object_model_id`
- `state_id`
- `state_name`
- `is_initial`

### 4.2 `prophet_transition_catalog`

Purpose:
- Runtime source of legal edges.

Columns:
- `object_model_id`
- `transition_id`
- `from_state_id`
- `to_state_id`

## 5. Generated JPA Components

Per object model:
- `<Object>Entity`
- `<Object>Repository`
- `<Object>StateHistoryEntity` (if stateful)
- `<Object>StateHistoryRepository`

Shared generated components:
- Action endpoint controller
- Query controllers (`GET /<objects>/{id}` and paginated/filterable `GET /<objects>`)
- Flyway and Liquibase migration resources (`db/migration`, `db/changelog`)

## 6. Canonical Type Map (v0.1)

- `string` -> `text`
- `int` -> `integer`
- `long` -> `bigint`
- `float` -> `real`
- `double` -> `double precision`
- `decimal` -> `numeric(precision, scale)` (default `numeric(18,2)`)
- `boolean` -> `boolean`
- `date` -> `date`
- `datetime` -> `timestamptz`
- `duration` -> `interval`

Java mapping:
- `text` -> `String`
- `numeric` -> `BigDecimal`
- `date` -> `LocalDate`
- `timestamptz` -> `OffsetDateTime`
- `interval` -> `Duration`

## 7. Deterministic Naming Rules

- Table names derive from ontology names with snake_case.
- Column names derive from field names with snake_case.
- FK names derive as `fk_<table>_<column>`.
- Index names derive as `idx_<table>_<column_list_hash>`.
- No random suffixes.

## 8. Compatibility Impact Rules (DB/JPA)

Breaking changes include:
- table drop/rename
- column drop/rename
- nullability tighten
- type narrowing
- enum/state value removal
- FK target change

Additive changes include:
- new nullable column
- new table
- new index
- new transition edge

## 9. Why This Layout

- Keeps domain data strongly typed and query-friendly.
- Preserves ontology semantics (states/transitions) in the database.
- Produces JPA code engineers can use directly.
- Keeps Seer-specific orchestration concerns outside generated service code.
