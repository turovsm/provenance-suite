from src.presentation.api.v1.auth import router as auth_router
from src.presentation.api.v1.music import router as music_router
from src.presentation.api.v1.user import router as user_router


__all__ = ["user_router", "auth_router", "music_router"]
