from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.presentation.api.v1 import user_router


app = FastAPI(
    title="Provenance Suite API",
    description="Core backend infrastructure to track media entities.",
    version="0.1.0",
)

# CORS and stuff
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4200", "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/v1")


@app.get("/health", tags=["System System Stability Checks"])
async def health_check():
    """System stability check endpoint."""
    return {"status": "healthy", "service": "provenance-core-backend", "version": "0.1.0"}
