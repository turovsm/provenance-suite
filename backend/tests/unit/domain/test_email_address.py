import pytest

from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects.email import EmailAddress


@pytest.mark.parametrize(
    "raw",
    [
        "user@vault.io",
        "first.last@vault.io",
        "user+tag@vault.io",
        "user_name%x@sub.domain.co.uk",
        "1234@numbers.net",
    ],
)
def test_valid_emails_accepted(raw: str) -> None:
    assert str(EmailAddress(raw)) == raw.lower()


def test_email_is_normalized_lowercase_and_trimmed() -> None:
    assert str(EmailAddress("  MiXeD@Vault.IO  ")) == "mixed@vault.io"


def test_equality_after_normalization() -> None:
    assert EmailAddress("USER@vault.io") == EmailAddress("user@VAULT.IO")


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "plainaddress",
        "@missing-local.io",
        "user@",
        "user@domain",
        "user@domain.i",
        "user @vault.io",
        "user@vault .io",
        "user@@vault.io",
    ],
)
def test_invalid_emails_rejected(raw: str) -> None:
    with pytest.raises(InvalidEmailError):
        EmailAddress(raw)


def test_immutability() -> None:
    email = EmailAddress("user@vault.io")
    with pytest.raises(AttributeError):
        email.value = "other@vault.io"
