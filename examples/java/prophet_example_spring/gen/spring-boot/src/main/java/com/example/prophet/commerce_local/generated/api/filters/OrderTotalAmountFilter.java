package com.example.prophet.commerce_local.generated.api.filters;

import javax.annotation.processing.Generated;
import java.math.BigDecimal;
import java.util.List;

@Generated("prophet-cli")
public record OrderTotalAmountFilter(
    BigDecimal eq,
    List<BigDecimal> in,
    BigDecimal gte,
    BigDecimal lte
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private BigDecimal eq;
        private List<BigDecimal> in;
        private BigDecimal gte;
        private BigDecimal lte;

        public Builder eq(BigDecimal value) {
            this.eq = value;
            return this;
        }

        public Builder in(List<BigDecimal> value) {
            this.in = value;
            return this;
        }

        public Builder gte(BigDecimal value) {
            this.gte = value;
            return this;
        }

        public Builder lte(BigDecimal value) {
            this.lte = value;
            return this;
        }
        public OrderTotalAmountFilter build() {
            return new OrderTotalAmountFilter(
                eq,
                in,
                gte,
                lte
            );
        }
    }
}
