from src.domain.value_objects.aliases import (
    MAX_ALIAS_LENGTH,
    MAX_ALIASES_PER_ENTITY,
    normalize_aliases,
)
from src.domain.value_objects.email import EmailAddress


__all__ = ["EmailAddress", "MAX_ALIASES_PER_ENTITY", "MAX_ALIAS_LENGTH", "normalize_aliases"]
