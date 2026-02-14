package com.example.prophet.generated.api.filters;

import javax.annotation.processing.Generated;
import java.util.List;

@Generated("prophet-cli")
public record OrderOrderIdFilter(
    String eq,
    List<String> in,
    String contains
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String eq;
        private List<String> in;
        private String contains;

        public Builder eq(String value) {
            this.eq = value;
            return this;
        }

        public Builder in(List<String> value) {
            this.in = value;
            return this;
        }

        public Builder contains(String value) {
            this.contains = value;
            return this;
        }
        public OrderOrderIdFilter build() {
            return new OrderOrderIdFilter(
                eq,
                in,
                contains
            );
        }
    }
}
