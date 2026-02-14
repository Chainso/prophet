package com.example.prophet.commerce_local.generated.mapping;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.User;
import com.example.prophet.commerce_local.generated.persistence.UserEntity;
import org.springframework.stereotype.Component;

@Component
@Generated("prophet-cli")
public class UserDomainMapper {
    public User toDomain(UserEntity entity) {
        if (entity == null) {
            return null;
        }
        return User.builder()
            .userId(entity.getUserId())
            .email(entity.getEmail())
            .build();
    }
}
