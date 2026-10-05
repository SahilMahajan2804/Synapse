package com.synapse.controller;

import com.synapse.llm.LlmGateway;
import com.synapse.privacy.PrivacyServiceGateway;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class SynapseControllerChatTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PrivacyServiceGateway privacyServiceGateway;

    @MockBean
    private LlmGateway llmGateway;

    @BeforeEach
    void setUp() {
        when(privacyServiceGateway.status()).thenReturn("UP");
        when(privacyServiceGateway.anonymize(anyString(), anyString())).thenReturn(
                new com.synapse.privacy.model.AnonymizedPayload(
                        "demo",
                        "Alex Morgan",
                        java.util.List.of(),
                        java.util.List.of(),
                        new com.synapse.privacy.model.LeakGuardReport(true, 0, java.util.List.of()),
                        new com.synapse.privacy.model.AnonymizeTiming(10, 8)
                )
        );
        when(privacyServiceGateway.deanonymize(anyString(), anyString())).thenReturn(
                new com.synapse.privacy.model.DeanonymizedPayload(
                        "demo",
                        "Rahul Sharma",
                        1,
                        12
                )
        );
        when(llmGateway.provider()).thenReturn("mock");
        when(llmGateway.generate(anyString())).thenReturn("Mock LLM answer");
    }

    @Test
    void chatEndpointReturnsProtectedResult() throws Exception {
        mockMvc.perform(multipart("/api/chat")
                        .param("text", "Rahul Sharma")
                        .param("sessionId", "demo"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.sessionId").value("demo"))
                .andExpect(jsonPath("$.syntheticText").value("Alex Morgan"))
                .andExpect(jsonPath("$.llmSyntheticResponse").value("Mock LLM answer"))
                .andExpect(jsonPath("$.restoredResponse").value("Rahul Sharma"));
    }
}
