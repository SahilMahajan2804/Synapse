package com.synapse.privacy.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

public record AnonymizedPayload(
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("synthetic_text") String syntheticText,
        @JsonProperty("entities") List<Map<String, Object>> entities,
        @JsonProperty("mappings") List<Map<String, Object>> mappings,
        @JsonProperty("leak_guard") LeakGuardReport leakGuard,
        @JsonProperty("timings") AnonymizeTiming timings
) {
}
