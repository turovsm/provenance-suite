import re
from dataclasses import dataclass

from src.domain.exceptions import InvalidEmailError


@dataclass(frozen=True, slots=True)
class EmailAddress:
    value: str

    _PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not self._PATTERN.match(normalized):
            msg = f"Provided value sequence '{self.value}' violates email specification layout."
            raise InvalidEmailError(msg)

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
