package com.example.prophet.generated.actions;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Address;
import com.example.prophet.generated.domain.UserRef;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

@Generated("prophet-cli")
public record CreateOrderCommand(
    @NotNull UserRef customer,
    String discountCode,
    @NotNull String orderId,
    Address shippingAddress,
    List<String> tags,
    @NotNull BigDecimal totalAmount
) {
}
