package com.example.prophet.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.generated.domain.Order;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record OrderListResponse(
    @NotNull List<Order> items,
    @NotNull int page,
    @NotNull int size,
    @NotNull long totalElements,
    @NotNull int totalPages
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private List<Order> items;
        private int page;
        private int size;
        private long totalElements;
        private int totalPages;

        public Builder items(List<Order> value) {
            this.items = value;
            return this;
        }

        public Builder page(int value) {
            this.page = value;
            return this;
        }

        public Builder size(int value) {
            this.size = value;
            return this;
        }

        public Builder totalElements(long value) {
            this.totalElements = value;
            return this;
        }

        public Builder totalPages(int value) {
            this.totalPages = value;
            return this;
        }
        public OrderListResponse build() {
            return new OrderListResponse(
                items,
                page,
                size,
                totalElements,
                totalPages
            );
        }
    }
}
