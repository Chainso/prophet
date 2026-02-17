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
- Transition service/handler/validator extension points

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

- generated services depend on `io.prophet.events.runtime.EventPublisher` from `io.github.chainso:prophet-events-runtime`.
- generated event payload ref fields use sealed `<Object>RefOrObject` contracts.
- generated default action services publish produced events (signals and transitions); emitted envelopes normalize embedded objects back to refs and include extracted snapshots in `updatedObjects`.
- generated `EventPublisherNoOp` is registered automatically when no custom publisher bean is provided.
- generated default action services publish action outcomes automatically after successful handler execution.
- handlers can return either the produced event payload directly or generated `ActionOutcome` with additional domain events.
- stateful objects generate transition handlers and validators:
  - default transition handler beans are emitted as `@Component` + `@ConditionalOnMissingBean`
  - transition methods return transition drafts seeded with object primary keys plus `fromState`/`toState`
  - handler defaults invoke `<ObjectName>TransitionValidator` before state mutation and fail with `TransitionValidationResult.failureReason` when validation fails

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
