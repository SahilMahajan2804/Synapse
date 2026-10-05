package com.synapse.controller;

import com.synapse.llm.LlmGateway;
import com.synapse.model.ChatResult;
import com.synapse.privacy.PrivacyServiceGateway;
import com.synapse.privacy.model.AnonymizedPayload;
import com.synapse.privacy.model.DeanonymizedPayload;
import jakarta.servlet.http.HttpServletRequest;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class SynapseController {
    private final PrivacyServiceGateway privacyServiceGateway;
    private final LlmGateway llmGateway;

    public SynapseController(PrivacyServiceGateway privacyServiceGateway, LlmGateway llmGateway) {
        this.privacyServiceGateway = privacyServiceGateway;
        this.llmGateway = llmGateway;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
                "status", "UP",
                "synapseService", privacyServiceGateway.status(),
                "llmProvider", llmGateway.provider(),
                "llmKeyConfigured", llmGateway.isKeyConfigured()
        );
    }

    @PostMapping(value = "/chat", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE, MediaType.APPLICATION_FORM_URLENCODED_VALUE})
    public ChatResult chat(
            @RequestParam(value = "sessionId", required = false) String sessionId,
            HttpServletRequest request
    ) {
        String resolvedText = resolveTextInput(request);
        if (resolvedText == null || resolvedText.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Add text or choose a PDF to continue.");
        }

        String effectiveSessionId = (sessionId == null || sessionId.isBlank()) ? UUID.randomUUID().toString() : sessionId;

        try {
            AnonymizedPayload anonymized = privacyServiceGateway.anonymize(resolvedText, effectiveSessionId);
            String llmSyntheticResponse = llmGateway.generate(anonymized.syntheticText());
            DeanonymizedPayload deanonymized = privacyServiceGateway.deanonymize(effectiveSessionId, llmSyntheticResponse);

            Map<String, Object> leakGuard = new LinkedHashMap<>();
            leakGuard.put("passed", anonymized.leakGuard() == null || anonymized.leakGuard().passed());
            leakGuard.put("leakedCount", anonymized.leakGuard() == null ? 0 : anonymized.leakGuard().leakedCount());
            leakGuard.put("leakedValues", anonymized.leakGuard() == null ? List.of() : anonymized.leakGuard().leakedValues());

            Map<String, Object> timingsMs = new LinkedHashMap<>();
            timingsMs.put("parse", 0);
            timingsMs.put("detect", anonymized.timings() == null ? 0 : anonymized.timings().detectMs());
            timingsMs.put("synthesize", anonymized.timings() == null ? 0 : anonymized.timings().synthesizeMs());
            timingsMs.put("llm", 0);
            timingsMs.put("restore", deanonymized.restoreMs());
            timingsMs.put("total", (anonymized.timings() == null ? 0 : anonymized.timings().detectMs() + anonymized.timings().synthesizeMs()) + deanonymized.restoreMs());

            return new ChatResult(
                    effectiveSessionId,
                    resolvedText,
                    anonymized.entities() == null ? List.of() : anonymized.entities(),
                    anonymized.syntheticText(),
                    llmSyntheticResponse,
                    deanonymized.restoredText(),
                    anonymized.mappings() == null ? List.of() : anonymized.mappings(),
                    leakGuard,
                    timingsMs
            );
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "The request could not be completed.");
        }
    }

    @DeleteMapping("/session/{sessionId}")
    public ResponseEntity<Map<String, String>> clearSession(@PathVariable String sessionId) {
        try {
            privacyServiceGateway.deleteSession(sessionId);
            return ResponseEntity.ok(Map.of("status", "OK"));
        } catch (ResponseStatusException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("status", "NOT_FOUND"));
        }
    }

    private String resolveTextInput(HttpServletRequest request) {
        String text = request.getParameter("text");
        if (text != null && !text.isBlank()) {
            return text;
        }

        try {
            for (var part : request.getParts()) {
                if (("text".equals(part.getName()) || "file".equals(part.getName())) && part.getSize() > 0) {
                    return extractText(part.getSubmittedFileName(), part.getInputStream().readAllBytes());
                }
            }
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "The uploaded payload could not be read.");
        }

        return null;
    }

    private String extractText(String filename, byte[] bytes) {
        try {
            String lowerName = filename == null ? "" : filename.toLowerCase();
            if (lowerName.endsWith(".pdf") || (bytes.length > 4 && bytes[0] == '%' && bytes[1] == 'P' && bytes[2] == 'D' && bytes[3] == 'F')) {
                return extractPdfText(bytes);
            }
            return new String(bytes, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "The uploaded file could not be processed.");
        }
    }

    private String extractPdfText(byte[] pdfBytes) throws IOException {
        try (PDDocument document = Loader.loadPDF(pdfBytes)) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        }
    }
}
