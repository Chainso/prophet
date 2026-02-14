# Regenerate via Spring Initializr

Use this if you want to recreate the example project from a fresh Spring Initializr output.

## Option A: start.spring.io UI

Set these fields:
- Project: `Gradle - Kotlin`
- Language: `Java`
- Spring Boot: `3.3.x`
- Group: `com.example`
- Artifact: `prophet_example_spring`
- Name: `prophet_example_spring`
- Packaging: `Jar`
- Java: `21`
- Dependencies:
  - `Spring Web`
  - `Validation`
  - `Spring Data JPA`
  - `PostgreSQL Driver`

Then generate and unzip into `examples/java`.

## Option B: Non-interactive command

```bash
curl -sSL "https://start.spring.io/starter.zip?type=gradle-project-kotlin&language=java&bootVersion=3.3.2&baseDir=prophet_example_spring&groupId=com.example&artifactId=prophet_example_spring&name=prophet_example_spring&packageName=com.example.prophet_example_spring&packaging=jar&javaVersion=21&dependencies=web,validation,data-jpa,postgresql" -o prophet_example_spring.zip
unzip prophet_example_spring.zip -d .
```

After generation, copy Prophet generated artifacts into the app:

```bash
cp -R ../gen/spring-boot/src/main/java/com/example/prophet/generated src/main/java/com/example/prophet/
cp ../gen/spring-boot/src/main/resources/application-prophet.yml src/main/resources/
cp ../gen/sql/schema.sql src/main/resources/
```
