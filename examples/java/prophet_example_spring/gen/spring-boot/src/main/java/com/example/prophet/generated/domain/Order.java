package com.example.prophet.generated.domain;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Address;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

@Generated("prophet-cli")
public record Order(
    @NotNull String orderId,
    @NotNull UserRef customer,
    @NotNull BigDecimal totalAmount,
    String discountCode,
    List<String> tags,
    Address shippingAddress,
    @NotNull OrderState currentState
) {
}
