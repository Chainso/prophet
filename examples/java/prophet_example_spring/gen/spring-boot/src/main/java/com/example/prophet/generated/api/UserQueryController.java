package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.User;
import com.example.prophet.generated.mapping.UserDomainMapper;
import com.example.prophet.generated.persistence.UserEntity;
import com.example.prophet.generated.persistence.UserRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/users")
@Generated("prophet-cli")
public class UserQueryController {

    private final UserRepository repository;
    private final UserDomainMapper mapper;

    public UserQueryController(UserRepository repository, UserDomainMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @GetMapping
    public ResponseEntity<UserListResponse> list(
        @RequestParam(name = "userId", required = false) String userId,
        @RequestParam(name = "email", required = false) String email,
        @PageableDefault(size = 20) Pageable pageable
    ) {
        Specification<UserEntity> spec = (root, query, cb) -> cb.conjunction();
        if (userId != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("userId"), userId));
        }
        if (email != null) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("email"), email));
        }
        Page<UserEntity> entityPage = repository.findAll(spec, pageable);
        List<User> items = entityPage.stream().map(mapper::toDomain).toList();
        UserListResponse result = UserListResponse.builder()
            .items(items)
            .page(entityPage.getNumber())
            .size(entityPage.getSize())
            .totalElements(entityPage.getTotalElements())
            .totalPages(entityPage.getTotalPages())
            .build();
        return ResponseEntity.ok(result);
    }

    @GetMapping("/{userId}")
    public ResponseEntity<User> getById(@PathVariable("userId") String userId) {
        Optional<UserEntity> maybeEntity = repository.findById(userId);
        if (maybeEntity.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        User domain = mapper.toDomain(maybeEntity.get());
        return ResponseEntity.ok(domain);
    }
}
