package com.example.prophet.generated.api.filters;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.OrderState;
import java.util.List;

@Generated("prophet-cli")
public record OrderCurrentStateFilter(
    OrderState eq,
    List<OrderState> in
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private OrderState eq;
        private List<OrderState> in;

        public Builder eq(OrderState value) {
            this.eq = value;
            return this;
        }

        public Builder in(List<OrderState> value) {
            this.in = value;
            return this;
        }
        public OrderCurrentStateFilter build() {
            return new OrderCurrentStateFilter(
                eq,
                in
            );
        }
    }
}
