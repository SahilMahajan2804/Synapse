from app.detection.verhoeff import check_digit, is_valid


def test_required_verhoeff_vectors() -> None:
    assert is_valid("2363")
    assert check_digit("236") == 3
    assert is_valid("234567890124")
    assert not is_valid("234567890123")
