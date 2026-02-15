# Java Quickstart (Spring + JPA)

Use this guide when your application stack is Spring Boot + Spring Data JPA.

## 1. Configure `prophet.yaml`

```yaml
project:
  ontology_file: ontology/local/main.prophet

generation:
  out_dir: gen
  stack:
    id: java_spring_jpa
  targets: [sql, openapi, spring_boot, manifest]
  spring_boot:
    base_package: com.example

compatibility:
  baseline_ir: .prophet/baselines/main.ir.json
```

## 2. Generate and Wire Gradle

From your Spring project root:

```bash
prophet validate
prophet gen --wire-gradle
```

`--wire-gradle` updates Gradle config to include `:prophet_generated` and dependency wiring.

## 3. Implement Action Handlers

Generated handlers are stubs by design. Replace stub implementations in your app-owned code by implementing generated interfaces from:
- `gen/spring-boot/src/main/java/.../generated/service/handler/`

## 4. Optionally Implement Event Emission

Generated action services emit action outputs through the generated event emitter interface.
Provide your own emitter bean to connect to your platform event bus. If you do nothing, generated no-op emitter wiring is used.

## 5. Run Compile/Test Gates

```bash
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
prophet check --show-reasons
```

## 6. Run the Service

```bash
./gradlew bootRun
```

Default local example setup uses embedded H2. Configure your production datasource in your application config.

## Reference

- Spring integration details: [Spring Boot Reference](../reference/spring-boot.md)
- Query/action contracts: [Generation Reference](../reference/generation.md)
