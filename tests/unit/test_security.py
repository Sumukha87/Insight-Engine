"""
Unit tests for src/backend/auth/security.py

Tests password hashing, JWT creation/decode, and token hashing.
All tests run without any external services.
"""
import pytest
from jose import JWTError

from src.backend.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)

SAMPLE_PW = "correcthorsebatterystaple"
OTHER_PW = "wrongpassword"


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password(SAMPLE_PW)
        assert hashed != SAMPLE_PW

    def test_correct_password_verifies(self):
        hashed = hash_password(SAMPLE_PW)
        assert verify_password(SAMPLE_PW, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password(SAMPLE_PW)
        assert verify_password(OTHER_PW, hashed) is False

    def test_different_hashes_for_same_password(self):
        # bcrypt uses random salt — two hashes of same password must differ
        h1 = hash_password(SAMPLE_PW)
        h2 = hash_password(SAMPLE_PW)
        assert h1 != h2

    def test_short_input_hashes_correctly(self):
        # hash_password itself doesn't enforce length — that's Pydantic's job
        hashed = hash_password("abc")
        assert verify_password("abc", hashed) is True


class TestJWT:
    def test_create_and_decode(self):
        import uuid
        user_id = str(uuid.uuid4())
        token = create_access_token(subject=user_id)
        decoded_id = decode_token(token)
        assert decoded_id == user_id

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises(self):
        token = create_access_token(subject="user-123")
        # Flip the last character
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_token_contains_subject(self):
        token = create_access_token(subject="test-subject")
        subject = decode_token(token)
        assert subject == "test-subject"


class TestHashToken:
    def test_deterministic(self):
        assert hash_token("abc123") == hash_token("abc123")

    def test_length_is_64(self):
        # SHA-256 hex digest is always 64 characters
        assert len(hash_token("anything")) == 64

    def test_different_inputs_produce_different_hashes(self):
        assert hash_token("token_a") != hash_token("token_b")

    def test_empty_string_hashes(self):
        result = hash_token("")
        assert len(result) == 64
