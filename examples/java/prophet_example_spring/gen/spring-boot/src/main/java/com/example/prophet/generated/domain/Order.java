package com.example.prophet.generated.domain;

import com.example.prophet.generated.domain.Address;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

public record Order(
    @NotNull UserRef customer,
    String discountCode,
    @NotNull String orderId,
    Address shippingAddress,
    List<String> tags,
    @NotNull BigDecimal totalAmount,
    @NotNull OrderState currentState
) {
}
