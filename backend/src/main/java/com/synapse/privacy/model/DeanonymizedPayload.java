package com.synapse.privacy.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record DeanonymizedPayload(
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("restored_text") String restoredText,
        @JsonProperty("replacements") int replacements,
        @JsonProperty("restore_ms") int restoreMs
) {
}
