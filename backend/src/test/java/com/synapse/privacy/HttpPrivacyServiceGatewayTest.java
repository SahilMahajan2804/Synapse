package com.synapse.privacy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.synapse.config.SynapseProperties;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;
import org.springframework.web.server.ResponseStatusException;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

class HttpPrivacyServiceGatewayTest {
    @Test
    void anonymizeSendsSnakeCaseRequestFields() throws Exception {
        AtomicReference<String> requestBody = new AtomicReference<>();
        AtomicReference<String> contentType = new AtomicReference<>();
        AtomicReference<String> transferEncoding = new AtomicReference<>();
        AtomicReference<String> contentLength = new AtomicReference<>();
        AtomicReference<String> upgrade = new AtomicReference<>();
        AtomicReference<java.util.List<String>> internalKeys = new AtomicReference<>();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/v1/anonymize", exchange -> {
            requestBody.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            contentType.set(exchange.getRequestHeaders().getFirst("Content-Type"));
            transferEncoding.set(exchange.getRequestHeaders().getFirst("Transfer-Encoding"));
            contentLength.set(exchange.getRequestHeaders().getFirst("Content-Length"));
            upgrade.set(exchange.getRequestHeaders().getFirst("Upgrade"));
            internalKeys.set(exchange.getRequestHeaders().get("X-Internal-Key"));
            byte[] response = "{\"detail\":[]}".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(422, response.length);
            exchange.getResponseBody().write(response);
            exchange.close();
        });
        server.start();

        try {
            SynapseProperties properties = new SynapseProperties();
            properties.setPrivacyServiceUrl("http://127.0.0.1:" + server.getAddress().getPort());
            properties.setInternalKey("dev-key");
            HttpPrivacyServiceGateway gateway = new HttpPrivacyServiceGateway(properties, new ObjectMapper());

            assertThrows(ResponseStatusException.class, () -> gateway.anonymize("Hello world", "demo"));

            JsonNode body = new ObjectMapper().readTree(requestBody.get());
            assertEquals("demo", body.path("session_id").asText());
            assertEquals("Hello world", body.path("text").asText());
            assertFalse(body.has("sessionId"));
            assertEquals("application/json", contentType.get());
            assertNull(transferEncoding.get());
            assertEquals(Integer.toString(requestBody.get().getBytes(StandardCharsets.UTF_8).length), contentLength.get());
            assertNull(upgrade.get());
            assertEquals(java.util.List.of("dev-key"), internalKeys.get());
        } finally {
            server.stop(0);
        }
    }
}