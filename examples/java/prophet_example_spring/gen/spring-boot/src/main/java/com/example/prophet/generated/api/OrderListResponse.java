package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import java.util.List;
import com.example.prophet.generated.domain.Order;

@Generated("prophet-cli")
public record OrderListResponse(
    List<Order> items,
    int page,
    int size,
    long totalElements,
    int totalPages
) {
}
