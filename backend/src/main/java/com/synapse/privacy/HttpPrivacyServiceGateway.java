
package com.synapse.privacy;

import com.synapse.config.SynapseProperties;
import com.synapse.privacy.model.AnonymizedPayload;
import com.synapse.privacy.model.DeanonymizedPayload;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.client.JdkClientHttpRequestFactory;

import java.net.http.HttpClient;

@Component
public class HttpPrivacyServiceGateway implements PrivacyServiceGateway {
    private final SynapseProperties properties;
    private final RestClient restClient;
    private final ObjectMapper objectMapper;

    public HttpPrivacyServiceGateway(SynapseProperties properties, ObjectMapper objectMapper) {
        this.properties = properties;
        this.objectMapper = objectMapper;
        String baseUrl = properties.getPrivacyServiceUrl() == null || properties.getPrivacyServiceUrl().isBlank()
                ? "http://localhost:8000"
                : properties.getPrivacyServiceUrl();
        HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .defaultHeader("X-Internal-Key", properties.getInternalKey())
            .requestFactory(new JdkClientHttpRequestFactory(httpClient))
                .build();
    }

    @Override
    public String status() {
        try {
            restClient.get()
                    .uri("/health")
                    .retrieve()
                    .toBodilessEntity();
            return "UP";
        } catch (ResourceAccessException | HttpClientErrorException e) {
            return "DOWN";
        }
    }

    @Override
    public AnonymizedPayload anonymize(String text, String sessionId) {
        try {
            return restClient.post()
                    .uri("/v1/anonymize")
                    .header("X-Internal-Key", properties.getInternalKey())
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(toJsonBytes(new PrivacyRequest(sessionId, text)))
                    .retrieve()
                    .body(AnonymizedPayload.class);
        } catch (ResourceAccessException | HttpClientErrorException e) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Privacy service is unavailable.");
        }
    }

    @Override
    public DeanonymizedPayload deanonymize(String sessionId, String text) {
        try {
            return restClient.post()
                    .uri("/v1/deanonymize")
                    .header("X-Internal-Key", properties.getInternalKey())
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(toJsonBytes(new DeanonymizeRequest(sessionId, text)))
                    .retrieve()
                    .body(DeanonymizedPayload.class);
        } catch (ResourceAccessException | HttpClientErrorException e) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Privacy service is unavailable.");
        }
    }

    @Override
    public void deleteSession(String sessionId) {
        try {
            restClient.delete()
                    .uri("/v1/sessions/{sessionId}", sessionId)
                    .header("X-Internal-Key", properties.getInternalKey())
                    .retrieve()
                    .toBodilessEntity();
        } catch (ResourceAccessException | HttpClientErrorException e) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Session not found.");
        }
    }

    private record PrivacyRequest(String session_id, String text) {}

    private record DeanonymizeRequest(String session_id, String text) {}

    private byte[] toJsonBytes(Object payload) {
        try {
            return objectMapper.writeValueAsBytes(payload);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Could not serialize privacy-service request.", e);
        }
    }
}
