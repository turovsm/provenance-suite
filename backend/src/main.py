from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


@app.get("/health", tags=["System System Stability Checks"])
async def health_check():
    """System stability check endpoint."""
    return {"status": "healthy", "service": "provenance-core-backend", "version": "0.1.0"}
