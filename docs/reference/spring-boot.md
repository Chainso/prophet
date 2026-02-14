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

## Query APIs

- `GET /<objects>`: pagination/sort only
- `POST /<objects>/query`: typed filtering + pagination/sort
- `GET /<objects>/{id}` or composite key path segments

List responses are generated DTO envelopes (`*ListResponse`), not raw Spring `Page` payloads.

## Action APIs

- `POST /actions/<actionName>`
- request/response payloads map to generated `actionInput`/`actionOutput` contracts
- default generated handlers throw `UnsupportedOperationException`
- user implements handler/service beans in user-owned code

## Gradle Wiring

`prophet gen --wire-gradle` ensures:
- `settings.gradle(.kts)` includes `:prophet_generated`
- app module depends on `implementation(project(":prophet_generated"))`

`prophet clean` unwires these changes unless `--keep-gradle-wire` is used.

## Deep Dive

- `docs/prophet-spring-boot-golden-stack-v0.1.md`
- `docs/prophet-jpa-mapping-v0.1.md`
