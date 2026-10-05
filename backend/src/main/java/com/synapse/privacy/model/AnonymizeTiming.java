package com.synapse.privacy.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AnonymizeTiming(
        @JsonProperty("detect_ms") int detectMs,
        @JsonProperty("synthesize_ms") int synthesizeMs
) {
}
