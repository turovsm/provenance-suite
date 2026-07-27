import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jwt import encode

from src.config import settings
from src.infrastructure.crypto.token_manager import JwtTokenManager, TokenVerificationError


@pytest.fixture()
def manager() -> JwtTokenManager:
    return JwtTokenManager()


def test_generate_pair_produces_distinct_typed_tokens(manager: JwtTokenManager) -> None:
    subject = str(uuid.uuid4())
    access, refresh, family_id, refresh_jti = manager.generate_token_pair(subject=subject)

    access_claims = manager.decode_and_verify_token(access, expected_type="access")
    refresh_claims = manager.decode_and_verify_token(refresh, expected_type="refresh")

    assert access != refresh
    assert access_claims["sub"] == refresh_claims["sub"] == subject
    assert access_claims["jti"] != refresh_claims["jti"]
    assert refresh_claims["jti"] == refresh_jti
    assert refresh_claims["family_id"] == family_id


def test_generate_pair_reuses_provided_family_id(manager: JwtTokenManager) -> None:
    fam = str(uuid.uuid4())
    _, refresh, family_id, _ = manager.generate_token_pair(subject="s", family_id=fam)
    assert family_id == fam
    assert manager.decode_and_verify_token(refresh, expected_type="refresh")["family_id"] == fam


def test_extra_claims_cannot_override_reserved_claims(manager: JwtTokenManager) -> None:
    access, _, _, _ = manager.generate_token_pair(
        subject="real-subject",
        extra_claims={"sub": "spoofed", "type": "refresh", "custom": "ok"},
    )
    claims = manager.decode_and_verify_token(access, expected_type="access")
    assert claims["sub"] == "real-subject"
    assert claims["type"] == "access"
    assert claims["custom"] == "ok"


def test_decode_rejects_wrong_expected_type(manager: JwtTokenManager) -> None:
    access, refresh, _, _ = manager.generate_token_pair(subject="s")
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token(access, expected_type="refresh")
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token(refresh, expected_type="access")


def test_decode_rejects_expired_token(manager: JwtTokenManager) -> None:
    now = datetime.now(UTC)
    expired = encode(
        {
            "sub": "s",
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token(expired)


def test_decode_rejects_tampered_signature(manager: JwtTokenManager) -> None:
    access, _, _, _ = manager.generate_token_pair(subject="s")
    forged = encode(
        {
            "sub": "s",
            "jti": str(uuid.uuid4()),
            "type": "access",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "attacker-controlled-secret-key-that-is-long-enough-to-look-plausible!!",
        algorithm=settings.JWT_ALGORITHM,
    )
    assert forged != access
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token(forged)


@pytest.mark.parametrize("missing", ["exp", "iat", "sub", "jti"])
def test_decode_rejects_missing_required_claims(manager: JwtTokenManager, missing: str) -> None:
    claims = {
        "sub": "s",
        "jti": str(uuid.uuid4()),
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    del claims[missing]
    token = encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token(token)


def test_decode_rejects_garbage_input(manager: JwtTokenManager) -> None:
    with pytest.raises(TokenVerificationError):
        manager.decode_and_verify_token("definitely-not-a-jwt")
