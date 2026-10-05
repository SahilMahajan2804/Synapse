package com.synapse.model;

import java.util.List;
import java.util.Map;

public record ChatResult(
        String sessionId,
        String originalText,
        List<Map<String, Object>> entities,
        String syntheticText,
        String llmSyntheticResponse,
        String restoredResponse,
        List<Map<String, Object>> mappings,
        Map<String, Object> leakGuard,
        Map<String, Object> timingsMs
) {
}
