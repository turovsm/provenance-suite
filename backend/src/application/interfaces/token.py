from typing import Any, Protocol


class TokenService(Protocol):
    def generate_access_token(
        self, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> str: ...
