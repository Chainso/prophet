# Prophet Spring Boot Golden Stack v0.1

## 1. Goal

Provide a first-class Spring Boot integration where Prophet ontology contracts generate a usable server foundation with strong JPA alignment and explicit action APIs.

## 2. Runtime Baseline

- Java 21
- Spring Boot 3.x
- Gradle Kotlin DSL
- JPA + Spring Data
- OpenAPI for REST contracts

## 3. Generated Surfaces

1. Domain layer
- Object model records
- State enums
- Object reference records

2. Persistence layer
- JPA entities
- Spring Data repositories
- SQL schema output aligned with object/state mapping
- State history entities for stateful objects
- JSON-backed JPA converters for list fields
- JSON-backed JPA converters for struct fields

3. Action API contracts
- `actionInput`/`actionOutput` records generated as request/response DTOs
- Action handler interfaces generated per action
- Default action handler stubs generated per action (`@ConditionalOnMissingBean`) that throw `UnsupportedOperationException`
- Action controller endpoints (`POST /actions/<actionName>`) delegating to handler beans

4. Query API
- Object query controllers (`GET /<objects>/{id}` for single keys, `GET /<objects>/{k1}/{k2}/...` for composite keys) over generated repositories
- Paginated/filterable object query controllers (`GET /<objects>`) backed by JPA Specifications
- List endpoints return generated DTO envelopes (never raw JPA entities or raw Spring `Page` payloads)
- Filter query params are generated for scalar/object-ref/state fields plus paging params (`page`, `size`, `sort`);
  list/struct fields are not exposed as direct query filters

5. Spring wiring
- Generated config enabling entity/repository scanning for generated persistence package
- Generated migration resources under `src/main/resources/db/**` auto-detected from the app's existing migration stack
  (`flyway` and/or `liquibase` dependencies/plugins already present in the host Gradle project)

## 4. Ownership Boundary

Generated (tool-owned):
- `gen/spring-boot/src/main/java/.../generated/**`
- `gen/spring-boot/src/main/resources/**`

User-owned:
- Application code outside generated package
- Action handler bean implementations

Rule:
- Regeneration can overwrite only generated paths.
- User-owned files are never modified by generation.

## 5. Action Lifecycle

1. Caller invokes `POST /actions/<actionName>`.
2. Controller validates payload against generated `actionInput` record.
3. Controller resolves `<ActionName>ActionHandler` bean (user bean if present, otherwise generated default stub).
4. Handler executes business logic.
5. Controller returns generated `actionOutput` record.

If only the generated default stub exists, endpoint returns `501 Not Implemented`.

## 6. Determinism Requirements

- Stable package/file paths.
- Canonical ordering of fields/types/actions in generated output.
- Stable method signatures for unchanged ontology.
- OpenAPI schema must match generated action/object contracts.

## 7. Non-Goals (v0.1)

- Auto-implementing action business logic.
- Auto-inferred state transitions from action names.
- Event ingestion/dispatch runtime (owned by an external platform/runtime layer).
