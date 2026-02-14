package com.example.prophet.generated.config;

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Configuration
@EntityScan(basePackages = "com.example.prophet.generated.persistence")
@EnableJpaRepositories(basePackages = "com.example.prophet.generated.persistence")
public class GeneratedPersistenceConfig {
}
