package com.example.prophet.commerce_local.generated.domain;

import javax.annotation.processing.Generated;
import com.fasterxml.jackson.annotation.JsonValue;

@Generated("prophet-cli")
public enum OrderStatus {
    Created("Created"),
    Approved("Approved"),
    Shipped("Shipped");

    private final String value;

    OrderStatus(String value) {
        this.value = value;
    }

    @JsonValue
    public String value() {
        return value;
    }
}
