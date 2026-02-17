package com.example.prophet.commerce_local.generated.persistence;

import javax.annotation.processing.Generated;
import com.example.prophet.commerce_local.generated.domain.Address;
import com.example.prophet.commerce_local.generated.domain.OrderState;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

/**
 * Customer order aggregate.
 */
@Entity
@Table(name = "orders")
@Generated("prophet-cli")
public class OrderEntity {

    /**
     * Stable order identifier.
     */
    @Id
    @Column(name = "order_id", nullable = false)
    private String orderId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_user_id", nullable = false)
    private UserEntity customer;

    @Column(name = "total_amount", nullable = false)
    private BigDecimal totalAmount;

    @Column(name = "discount_code", nullable = true)
    private String discountCode;

    @Convert(converter = OrderTagsListConverter.class)
    @Column(name = "tags", nullable = true, columnDefinition = "text")
    private List<String> tags;

    @Convert(converter = OrderShippingAddressStructConverter.class)
    @Column(name = "shipping_address", nullable = true, columnDefinition = "text")
    private Address shippingAddress;

    @Column(name = "approved_by_user_id", nullable = true)
    private String approvedByUserId;

    @Convert(converter = OrderApprovalNotesListConverter.class)
    @Column(name = "approval_notes", nullable = true, columnDefinition = "text")
    private List<String> approvalNotes;

    @Column(name = "approval_reason", nullable = true)
    private String approvalReason;

    @Column(name = "shipping_carrier", nullable = true)
    private String shippingCarrier;

    @Column(name = "shipping_tracking_number", nullable = true)
    private String shippingTrackingNumber;

    @Convert(converter = OrderShippingPackageIdsListConverter.class)
    @Column(name = "shipping_package_ids", nullable = true, columnDefinition = "text")
    private List<String> shippingPackageIds;

    @Enumerated(EnumType.STRING)
    @Column(name = "__prophet_state", nullable = false)
    private OrderState state;

    @Version
    @Column(name = "row_version", nullable = false)
    private long rowVersion;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    void onCreate() {
        OffsetDateTime now = OffsetDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = OffsetDateTime.now();
    }

    public String getOrderId() {
        return orderId;
    }

    public void setOrderId(String orderId) {
        this.orderId = orderId;
    }

    public UserEntity getCustomer() {
        return customer;
    }

    public void setCustomer(UserEntity customer) {
        this.customer = customer;
    }

    public BigDecimal getTotalAmount() {
        return totalAmount;
    }

    public void setTotalAmount(BigDecimal totalAmount) {
        this.totalAmount = totalAmount;
    }

    public String getDiscountCode() {
        return discountCode;
    }

    public void setDiscountCode(String discountCode) {
        this.discountCode = discountCode;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }

    public Address getShippingAddress() {
        return shippingAddress;
    }

    public void setShippingAddress(Address shippingAddress) {
        this.shippingAddress = shippingAddress;
    }

    public String getApprovedByUserId() {
        return approvedByUserId;
    }

    public void setApprovedByUserId(String approvedByUserId) {
        this.approvedByUserId = approvedByUserId;
    }

    public List<String> getApprovalNotes() {
        return approvalNotes;
    }

    public void setApprovalNotes(List<String> approvalNotes) {
        this.approvalNotes = approvalNotes;
    }

    public String getApprovalReason() {
        return approvalReason;
    }

    public void setApprovalReason(String approvalReason) {
        this.approvalReason = approvalReason;
    }

    public String getShippingCarrier() {
        return shippingCarrier;
    }

    public void setShippingCarrier(String shippingCarrier) {
        this.shippingCarrier = shippingCarrier;
    }

    public String getShippingTrackingNumber() {
        return shippingTrackingNumber;
    }

    public void setShippingTrackingNumber(String shippingTrackingNumber) {
        this.shippingTrackingNumber = shippingTrackingNumber;
    }

    public List<String> getShippingPackageIds() {
        return shippingPackageIds;
    }

    public void setShippingPackageIds(List<String> shippingPackageIds) {
        this.shippingPackageIds = shippingPackageIds;
    }

    public OrderState getState() {
        return state;
    }

    public void setState(OrderState state) {
        this.state = state;
    }
}
