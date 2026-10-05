package com.synapse.privacy;

import com.synapse.privacy.model.AnonymizedPayload;
import com.synapse.privacy.model.DeanonymizedPayload;

public interface PrivacyServiceGateway {
    String status();

    AnonymizedPayload anonymize(String text, String sessionId);

    DeanonymizedPayload deanonymize(String sessionId, String text);

    void deleteSession(String sessionId);
}
