plugins {
    `java-library`
    `maven-publish`
    signing
}

group = "io.github.chainso"
version = "0.3.0"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
    withJavadocJar()
    withSourcesJar()
}

repositories {
    mavenCentral()
}

tasks.withType<Test> {
    useJUnitPlatform()
}

dependencies {
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.0")
}

publishing {
    publications {
        create<MavenPublication>("mavenJava") {
            from(components["java"])
            artifactId = "prophet-events-runtime"
            pom {
                name.set("prophet-events-runtime")
                description.set("Shared async EventPublisher runtime for Prophet generated Java stacks")
                url.set("https://github.com/Chainso/prophet")
                licenses {
                    license {
                        name.set("MIT")
                        url.set("https://opensource.org/licenses/MIT")
                    }
                }
                developers {
                    developer {
                        id.set("prophet")
                        name.set("Prophet Maintainers")
                    }
                }
                scm {
                    connection.set("scm:git:https://github.com/Chainso/prophet.git")
                    developerConnection.set("scm:git:ssh://git@github.com:Chainso/prophet.git")
                    url.set("https://github.com/Chainso/prophet")
                }
            }
        }
    }
    repositories {
        val sonatypeUsername = System.getenv("SONATYPE_USERNAME")
        val sonatypePassword = System.getenv("SONATYPE_PASSWORD")
        if (!sonatypeUsername.isNullOrBlank() && !sonatypePassword.isNullOrBlank()) {
            maven {
                name = "sonatype"
                val releasesUrl = uri("https://ossrh-staging-api.central.sonatype.com/service/local/staging/deploy/maven2/")
                val snapshotsUrl = uri("https://central.sonatype.com/repository/maven-snapshots/")
                url = if (version.toString().endsWith("SNAPSHOT")) snapshotsUrl else releasesUrl
                credentials {
                    username = sonatypeUsername
                    password = sonatypePassword
                }
            }
        }
    }
}

signing {
    val signingKey = System.getenv("MAVEN_GPG_PRIVATE_KEY")
    val signingPassphrase = System.getenv("MAVEN_GPG_PASSPHRASE")
    if (!signingKey.isNullOrBlank()) {
        useInMemoryPgpKeys(signingKey, signingPassphrase)
        sign(publishing.publications["mavenJava"])
    }
}
