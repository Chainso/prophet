# Prophet Quickstart

This guide is for first-time users who want to generate and run working Prophet integrations.

## 1. Install CLI

Install from PyPI:

```bash
python3 -m pip install --upgrade prophet-cli
prophet --help
```

Or install from this repository for local development:

```bash
python3 -m venv .venv --system-site-packages
.venv/bin/pip install --no-build-isolation -e ./prophet-cli
```

If `prophet` is not on your PATH, use `.venv/bin/prophet` in commands below.

## 2. Java Quickstart (Spring + JPA)

```bash
cd examples/java/prophet_example_spring
prophet validate
prophet gen --wire-gradle
```

Expected outcome:
- `gen/sql/schema.sql`
- `gen/openapi/openapi.yaml`
- `gen/spring-boot/**`
- `.prophet/ir/current.ir.json`

## 3. Run Verification Gates

```bash
cd examples/java/prophet_example_spring
prophet check --show-reasons
./gradlew :prophet_generated:compileJava compileJava
./gradlew test
```

Expected outcome:
- `prophet check` reports no validation/compatibility drift issues
- Gradle compile and tests pass

## 4. Run the App

```bash
cd examples/java/prophet_example_spring
./gradlew bootRun
```

Default runtime profile uses embedded H2.

## 5. Explore Generated APIs

Object APIs:
- `GET /orders`
- `POST /orders/query`
- `GET /orders/{orderId}`
- `GET /users`
- `POST /users/query`
- `GET /users/{userId}`

Action APIs:
- `POST /actions/createOrder`
- `POST /actions/approveOrder`
- `POST /actions/shipOrder`

## 6. Node Quickstart (Express + Prisma)

```bash
cd examples/node/prophet_example_express_prisma
prophet gen
export DATABASE_URL="file:./dev.db"
npm install
npm run prisma:generate
npm run prisma:push
npm run dev
```

Expected outcome:
- `gen/node-express/src/generated/**`
- `gen/node-express/prisma/schema.prisma`
- `gen/openapi/openapi.yaml`
- `gen/manifest/node-autodetect.json`
- running Express app with generated repositories + concrete example handlers

## 7. Node Quickstart (Express + TypeORM)

```bash
cd examples/node/prophet_example_express_typeorm
prophet gen
npm install
npm run dev
```

Expected outcome:
- `gen/node-express/src/generated/**`
- `gen/node-express/src/generated/typeorm-entities.ts`
- `gen/openapi/openapi.yaml`
- `gen/manifest/node-autodetect.json`
- running Express app with SQLite-backed TypeORM repositories

Important:
- The example app uses SQLite + `synchronize: true` for local demo speed.
- For production, configure your `DataSource` from environment and set `synchronize: false`.
- Prophet owns generated entities/adapters; your app owns DB driver/connection/pooling/SSL config.

## 8. Node Quickstart (Express + Mongoose)

```bash
cd examples/node/prophet_example_express_mongoose
prophet gen
npm ci
export MONGO_URL="mongodb://127.0.0.1:27017/prophet_example_mongoose"
npm run dev
```

Expected outcome:
- `gen/node-express/src/generated/**`
- `gen/node-express/src/generated/mongoose-models.ts`
- `gen/node-express/src/generated/mongoose-adapters.ts`
- `gen/openapi/openapi.yaml`
- `gen/manifest/node-autodetect.json`
- running Express app with MongoDB-backed generated repositories

## Next Reads

- Full CLI reference: [CLI](../reference/cli.md)
- DSL reference: [DSL](../reference/dsl.md)
- Spring integration details: [Spring Boot](../reference/spring-boot.md)
- Node integration details: [Node/Express](../reference/node-express.md)
- Troubleshooting: [Troubleshooting](../reference/troubleshooting.md)
