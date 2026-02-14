package com.example.prophet.generated.persistence;

import javax.annotation.processing.Generated;
import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

@Generated("prophet-cli")
public interface UserRepository extends JpaRepository<UserEntity, String>, JpaSpecificationExecutor<UserEntity> {
}
