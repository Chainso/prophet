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
- Action controller endpoints (`POST /actions/<actionName>`) delegating to handler beans

4. Query API
- Object query controllers (`GET /<objects>/{id}`) over generated repositories

5. Spring wiring
- Generated config enabling entity/repository scanning for generated persistence package

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
3. Controller resolves user-provided `<ActionName>ActionHandler` bean.
4. Handler executes business logic.
5. Controller returns generated `actionOutput` record.

If handler bean is absent, endpoint returns `501 Not Implemented`.

## 6. Determinism Requirements

- Stable package/file paths.
- Canonical ordering of fields/types/actions in generated output.
- Stable method signatures for unchanged ontology.
- OpenAPI schema must match generated action/object contracts.

## 7. Non-Goals (v0.1)

- Auto-implementing action business logic.
- Auto-inferred state transitions from action names.
- Event ingestion/dispatch runtime (owned by Seer platform).
