import pytest

from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects.email import EmailAddress


def test_email_address_normalization_invariant() -> None:
    """Confirms text values normalize down to lowercase and strip dangling spaces."""
    raw_input = "  PRESERVATION@Vault.IO  "
    email_vo = EmailAddress(raw_input)
    assert str(email_vo) == "preservation@vault.io"


@pytest.mark.parametrize(
    "malformed_sequence",
    [
        "missing_domain.com",
        "email_at_domain_missing_tld@",
        "@missing_recipient.org",
        "spaces inside@domain.com",
    ],
)
def test_email_validation_rejection_invariant(malformed_sequence: str) -> None:
    """Guarantees structural address violations trigger an immediate InvalidEmailError block."""
    with pytest.raises(InvalidEmailError):
        EmailAddress(malformed_sequence)
