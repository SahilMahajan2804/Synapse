package com.synapse.privacy.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record LeakGuardReport(
        @JsonProperty("passed") boolean passed,
        @JsonProperty("leaked_count") int leakedCount,
        @JsonProperty("leaked_values") List<String> leakedValues
) {
}
