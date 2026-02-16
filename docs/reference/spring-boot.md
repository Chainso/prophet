# Spring Boot Integration Reference

## Runtime Baseline

- Java 21
- Spring Boot 3.x
- Spring Data JPA
- Gradle Kotlin DSL

## Package Namespace

Generated Java package root:
- `<generation.spring_boot.base_package>.<ontology_name>.generated`

Example:
- `com.example.prophet.commerce_local.generated`

## Generated Layers

- Domain records and enums
- JPA entities/repositories
- Mapping layer (`generated.mapping.*DomainMapper`)
- Query controllers
- Action contracts and action endpoints
- Action service/handler extension points

## JPA Mapping Rules

- Each ontology object maps to a typed table and JPA entity.
- Required fields map to non-null columns.
- Object refs map to relational associations where supported.
- Struct/list fields use generated converter-backed storage.
- Stateful objects include generated state and transition-history persistence support.

## Query APIs

- `GET /<objects>`: pagination/sort only
- `POST /<objects>/query`: typed filtering + pagination/sort
- `GET /<objects>/{id}` or composite key path segments

List responses are generated DTO envelopes (`*ListResponse`), not raw Spring `Page` payloads.

## Action APIs

- `POST /actions/<actionName>`
- request/response payloads map to generated action input/output contracts
- default generated handlers throw `UnsupportedOperationException`
- user implements handler/service beans in user-owned code

## Event Publisher APIs

- generated services depend on `io.prophet.events.runtime.EventPublisher` from `io.prophet:prophet-events-runtime`.
- generated `GeneratedEventPublisherNoOp` is registered automatically when no custom publisher bean is provided.
- generated default action services publish action outcomes automatically after successful handler execution.
- handlers can return either the action output directly or generated `ActionOutcome` with additional domain events.
- signal and transition emission remains user-controlled via generated event helpers.

## Ownership Boundaries

Generated (tool-owned):
- `gen/spring-boot/src/main/java/**`
- `gen/spring-boot/src/main/resources/**`

User-owned:
- application code outside generated package paths
- custom action handler/service implementations

## Gradle Wiring

`prophet gen --wire-gradle` ensures:
- `settings.gradle(.kts)` includes `:prophet_generated`
- app module depends on `implementation(project(":prophet_generated"))`

`prophet clean` unwires these changes unless `--keep-gradle-wire` is used.
