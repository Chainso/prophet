package com.example.prophet.commerce_local.generated.persistence;

import javax.annotation.processing.Generated;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;

@Entity
@Table(name = "order_state_history")
@Generated("prophet-cli")
public class OrderStateHistoryEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "history_id")
    private Long historyId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    private OrderEntity order;

    @Column(name = "transition_id", nullable = false)
    private String transitionId;

    @Column(name = "from_state", nullable = false)
    private String fromState;

    @Column(name = "to_state", nullable = false)
    private String toState;

    @Column(name = "changed_at", nullable = false)
    private OffsetDateTime changedAt;

    @Column(name = "changed_by")
    private String changedBy;

    @PrePersist
    void onCreate() {
        if (changedAt == null) {
            changedAt = OffsetDateTime.now();
        }
    }

    public void setOrder(OrderEntity value) {
        this.order = value;
    }

    public void setTransitionId(String transitionId) {
        this.transitionId = transitionId;
    }

    public void setFromState(String fromState) {
        this.fromState = fromState;
    }

    public void setToState(String toState) {
        this.toState = toState;
    }

    public void setChangedBy(String changedBy) {
        this.changedBy = changedBy;
    }
}
