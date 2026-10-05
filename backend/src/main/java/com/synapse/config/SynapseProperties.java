package com.synapse.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "synapse")
public class SynapseProperties {
    private String internalKey = "dev-key";
    private String privacyServiceUrl = "http://localhost:8000";
    private String llmProvider = "mock";
    private long requestTimeoutMs = 30_000L;
    private Cors cors = new Cors();

    public String getInternalKey() {
        return internalKey;
    }

    public void setInternalKey(String internalKey) {
        this.internalKey = internalKey;
    }

    public String getPrivacyServiceUrl() {
        return privacyServiceUrl;
    }

    public void setPrivacyServiceUrl(String privacyServiceUrl) {
        this.privacyServiceUrl = privacyServiceUrl;
    }

    public String getLlmProvider() {
        return llmProvider;
    }

    public void setLlmProvider(String llmProvider) {
        this.llmProvider = llmProvider;
    }

    public long getRequestTimeoutMs() {
        return requestTimeoutMs;
    }

    public void setRequestTimeoutMs(long requestTimeoutMs) {
        this.requestTimeoutMs = requestTimeoutMs;
    }

    public Cors getCors() {
        return cors;
    }

    public void setCors(Cors cors) {
        this.cors = cors;
    }

    public static class Cors {
        private String[] allowedOrigins = {"http://localhost:5173", "http://127.0.0.1:5173"};

        public String[] getAllowedOrigins() {
            return allowedOrigins;
        }

        public void setAllowedOrigins(String[] allowedOrigins) {
            this.allowedOrigins = allowedOrigins;
        }
    }
}
