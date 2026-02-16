package com.example.prophet.commerce_local.generated.config;

import javax.annotation.processing.Generated;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Configuration
@EntityScan(basePackages = "com.example.prophet.commerce_local.generated.persistence")
@EnableJpaRepositories(basePackages = "com.example.prophet.commerce_local.generated.persistence")
@Generated("prophet-cli")
public class PersistenceConfig {
}
