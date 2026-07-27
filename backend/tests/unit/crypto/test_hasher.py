import pytest

from src.infrastructure.crypto.hasher import PasswordHasherEngine


@pytest.fixture(scope="module")
def engine() -> PasswordHasherEngine:
    return PasswordHasherEngine()


def test_hash_and_verify_roundtrip(engine: PasswordHasherEngine) -> None:
    hashed = engine.hash_password("my-secret-password")
    assert engine.verify_password(hashed, "my-secret-password") is True


def test_verify_rejects_wrong_password(engine: PasswordHasherEngine) -> None:
    hashed = engine.hash_password("my-secret-password")
    assert engine.verify_password(hashed, "not-my-password") is False


def test_hash_is_salted_and_non_deterministic(engine: PasswordHasherEngine) -> None:
    assert engine.hash_password("same-input") != engine.hash_password("same-input")


def test_hash_never_contains_plaintext(engine: PasswordHasherEngine) -> None:
    password = "super-unique-plaintext-marker"
    assert password not in engine.hash_password(password)


def test_verify_rejects_corrupted_hash_string(engine: PasswordHasherEngine) -> None:
    assert engine.verify_password("$argon2id$corrupted", "anything") is False


def test_dummy_verification_runs_and_caches(engine: PasswordHasherEngine) -> None:
    PasswordHasherEngine._dummy_hash_cache = None
    engine.perform_dummy_verification()
    first_cache = PasswordHasherEngine._dummy_hash_cache
    assert first_cache is not None

    engine.perform_dummy_verification()
    assert PasswordHasherEngine._dummy_hash_cache is first_cache


def test_long_unicode_password_roundtrip(engine: PasswordHasherEngine) -> None:
    password = "пароль-密码-🎵" * 8
    hashed = engine.hash_password(password)
    assert engine.verify_password(hashed, password) is True
