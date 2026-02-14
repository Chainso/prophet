# Changelog

All notable changes to `prophet-cli` are documented in this file.

## [0.1.0] - 2026-02-14

### Added
- Prophet DSL parser and validator with compatibility-aware IR generation.
- Deterministic code generation targets for SQL, OpenAPI, Spring Boot module, Flyway, and Liquibase.
- Spring Boot golden-path output with generated:
  - domain records and action contracts,
  - action endpoint controllers and handler interfaces,
  - JPA entities/repositories and pagination/filter query APIs.
- Gradle multi-module wiring and unwiring support (`prophet gen --wire-gradle`, `prophet clean`).
- Snapshot and end-to-end integration tests for generator and CLI flows.
- Migration runtime autodetection warnings for host Gradle projects.
- Java record builder generation and builder-based query DTO/domain mapping.

### Notes
- This is the first release baseline for Prophet tooling.
