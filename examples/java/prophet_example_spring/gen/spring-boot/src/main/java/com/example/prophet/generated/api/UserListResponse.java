package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import java.util.List;
import com.example.prophet.generated.domain.User;

@Generated("prophet-cli")
public record UserListResponse(
    List<User> items,
    int page,
    int size,
    long totalElements,
    int totalPages
) {
}
