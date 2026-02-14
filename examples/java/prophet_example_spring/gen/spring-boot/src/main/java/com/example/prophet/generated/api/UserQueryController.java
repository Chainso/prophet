package com.example.prophet.generated.api;

import com.example.prophet.generated.domain.User;
import com.example.prophet.generated.persistence.UserEntity;
import com.example.prophet.generated.persistence.UserRepository;
import java.util.Optional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users")
public class UserQueryController {

    private final UserRepository repository;

    public UserQueryController(UserRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/{userId}")
    public ResponseEntity<User> getById(@PathVariable("userId") String userId) {
        Optional<UserEntity> maybeEntity = repository.findById(userId);
        if (maybeEntity.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        UserEntity entity = maybeEntity.get();
        User domain = new User(
            entity.getEmail(),
            entity.getUserId()
        );
        return ResponseEntity.ok(domain);
    }
}
