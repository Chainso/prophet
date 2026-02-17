<p align="center">
  <img src="https://raw.githubusercontent.com/Chainso/prophet/main/brand/exports/logo-horizontal-color.png" alt="Prophet logo" />
</p>

---

# io.github.chainso:prophet-events-runtime

`io.github.chainso:prophet-events-runtime` is the shared Java runtime contract used by Prophet-generated Spring action services.

Main project repository:
- https://github.com/Chainso/prophet

It defines:
- an async `EventPublisher` interface (`CompletionStage<Void>`)
- a canonical `EventWireEnvelope` record
- utility helpers (`EventIds.createEventId`, `EventTime.nowIso`)
- a `NoOpEventPublisher` for local wiring and tests

## Install

Maven:

```xml
<dependency>
  <groupId>io.github.chainso</groupId>
  <artifactId>prophet-events-runtime</artifactId>
  <version>0.2.9</version>
</dependency>
```

Gradle:

```kotlin
implementation("io.github.chainso:prophet-events-runtime:0.2.9")
```

## API

```java
public interface EventPublisher {
    CompletionStage<Void> publish(EventWireEnvelope envelope);
    CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes);
}
```

```java
public record EventWireEnvelope(
    String eventId,
    String traceId,
    String eventType,
    String schemaVersion,
    String occurredAt,
    String source,
    Map<String, Object> payload,
    Map<String, String> attributes
) {}
```

Core classes:
- `io.prophet.events.runtime.EventPublisher`
- `io.prophet.events.runtime.EventWireEnvelope`
- `io.prophet.events.runtime.NoOpEventPublisher`
- `io.prophet.events.runtime.EventIds`
- `io.prophet.events.runtime.EventTime`

## Implement a Platform Publisher

```java
import io.prophet.events.runtime.EventPublisher;
import io.prophet.events.runtime.EventWireEnvelope;
import java.util.List;
import java.util.concurrent.CompletionStage;

public final class PlatformEventPublisher implements EventPublisher {
    private final PlatformClient client;

    public PlatformEventPublisher(PlatformClient client) {
        this.client = client;
    }

    @Override
    public CompletionStage<Void> publish(EventWireEnvelope envelope) {
        return client.sendEvent(envelope);
    }

    @Override
    public CompletionStage<Void> publishBatch(List<EventWireEnvelope> envelopes) {
        return client.sendEvents(envelopes);
    }
}
```

## With Prophet-Generated Code

Generated Spring action services depend on this runtime and publish event wire envelopes after successful handler execution.
If no custom publisher bean is provided, generated code can fall back to a no-op publisher for local wiring.

## Local Validation

From repository root:

```bash
cd examples/java/prophet_example_spring
./gradlew -p ../../../prophet-lib/java test
./gradlew -p ../../../prophet-lib/java publishToMavenLocal
```

## More Information

- Main repository README: https://github.com/Chainso/prophet#readme
- Runtime index: https://github.com/Chainso/prophet/tree/main/prophet-lib
- Event wire contract: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-contract.md
- Event wire JSON schema: https://github.com/Chainso/prophet/tree/main/prophet-lib/specs/wire-event-envelope.schema.json
- Spring integration reference: https://github.com/Chainso/prophet/tree/main/docs/reference/spring-boot.md
- Example app: https://github.com/Chainso/prophet/tree/main/examples/java/prophet_example_spring
