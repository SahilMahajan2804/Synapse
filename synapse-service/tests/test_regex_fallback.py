from app.detection.regex_fallback import RegexFallbackDetector


def test_indian_phone_formats() -> None:
    detector = RegexFallbackDetector()
    samples = (
        "+91 98765 43210",
        "+91-98765-43210",
        "9876543210",
        "09876543210",
    )

    for sample in samples:
        entities = detector.detect(sample)
        assert [(entity.type, entity.text, entity.score) for entity in entities] == [
            ("PHONE_NUMBER", sample, 0.75)
        ]


def test_email_and_pan_patterns() -> None:
    entities = RegexFallbackDetector().detect("rahul.sharma@gmail.com ABCPX1234F")

    assert [(entity.type, entity.text) for entity in entities] == [
        ("EMAIL_ADDRESS", "rahul.sharma@gmail.com"),
        ("IN_PAN", "ABCPX1234F"),
    ]
    assert entities[0].score == 0.9
    assert entities[1].score == 0.85


def test_aadhaar_checksum_and_invalid_context() -> None:
    detector = RegexFallbackDetector()

    assert [(entity.type, entity.score) for entity in detector.detect("2345 6789 0124")] == [
        ("IN_AADHAAR", 0.9)
    ]
    assert detector.detect("2345 6789 0123") == []
    contextual = detector.detect("Aadhaar number: 2345 6789 0123")
    assert [(entity.type, entity.score) for entity in contextual] == [("IN_AADHAAR", 0.6)]
