package io.prophet.events.runtime;

/**
 * Result contract returned by generated transition validators.
 *
 * @param passesValidation true when transition validation passed
 * @param failureReason optional failure reason; null when validation passed
 */
public record TransitionValidationResult(boolean passesValidation, String failureReason) {
    /**
     * Creates a passing validation result.
     *
     * @return passing result
     */
    public static TransitionValidationResult passed() {
        return new TransitionValidationResult(true, null);
    }

    /**
     * Creates a failing validation result with a reason.
     *
     * @param failureReason failure reason
     * @return failing result
     */
    public static TransitionValidationResult failed(String failureReason) {
        return new TransitionValidationResult(false, failureReason);
    }
}
