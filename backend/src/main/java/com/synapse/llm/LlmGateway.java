package com.synapse.llm;

public interface LlmGateway {
    String provider();

    default boolean isKeyConfigured() {
        return false;
    }

    String generate(String syntheticText);
}
