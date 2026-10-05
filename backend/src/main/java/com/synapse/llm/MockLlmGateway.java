package com.synapse.llm;

import com.synapse.config.SynapseProperties;
import org.springframework.stereotype.Component;

@Component
public class MockLlmGateway implements LlmGateway {
    private final SynapseProperties properties;

    public MockLlmGateway(SynapseProperties properties) {
        this.properties = properties;
    }

    @Override
    public String provider() {
        return properties.getLlmProvider() == null || properties.getLlmProvider().isBlank() ? "mock" : properties.getLlmProvider();
    }

    @Override
    public boolean isKeyConfigured() {
        return true;
    }

    @Override
    public String generate(String syntheticText) {
        if (syntheticText == null || syntheticText.isBlank()) {
            return "No synthetic text was provided.";
        }
        return "Mock LLM response for: " + syntheticText;
    }
}
