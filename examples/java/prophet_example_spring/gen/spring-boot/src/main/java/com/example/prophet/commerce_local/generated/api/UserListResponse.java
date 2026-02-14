package com.example.prophet.commerce_local.generated.api;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.User;
import jakarta.validation.constraints.NotNull;
import java.util.List;

@Generated("prophet-cli")
public record UserListResponse(
    @NotNull List<User> items,
    @NotNull int page,
    @NotNull int size,
    @NotNull long totalElements,
    @NotNull int totalPages
) {

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private List<User> items;
        private int page;
        private int size;
        private long totalElements;
        private int totalPages;

        public Builder items(List<User> value) {
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
        public UserListResponse build() {
            return new UserListResponse(
                items,
                page,
                size,
                totalElements,
                totalPages
            );
        }
    }
}
