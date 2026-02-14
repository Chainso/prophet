package com.example.prophet.commerce_local.generated.api.filters;

import javax.annotation.processing.Generated;
import java.util.List;

@Generated("prophet-cli")
public record OrderCustomerFilter(
    String eq,
    List<String> in
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String eq;
        private List<String> in;

        public Builder eq(String value) {
            this.eq = value;
            return this;
        }

        public Builder in(List<String> value) {
            this.in = value;
            return this;
        }
        public OrderCustomerFilter build() {
            return new OrderCustomerFilter(
                eq,
                in
            );
        }
    }
}
