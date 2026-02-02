"""Nebulus Intelligence - Data Intelligence Service.

A reusable data intelligence platform with vertical templates for
multi-source data analysis, domain knowledge management, and
strategic recommendations.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from intelligence.api import data, query

# Configuration
BRAIN_URL = os.getenv("BRAIN_URL", "http://localhost:8080")
TEMPLATE = os.getenv("INTELLIGENCE_TEMPLATE", "dealership")
STORAGE_PATH = Path(__file__).parent / "storage"
DB_PATH = STORAGE_PATH / "databases"
VECTOR_PATH = STORAGE_PATH / "vectors"
KNOWLEDGE_PATH = STORAGE_PATH / "knowledge"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup, cleanup on shutdown."""
    # Ensure storage directories exist
    DB_PATH.mkdir(parents=True, exist_ok=True)
    VECTOR_PATH.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_PATH.mkdir(parents=True, exist_ok=True)

    print("Intelligence service starting...")
    print(f"  Template: {TEMPLATE}")
    print(f"  Brain URL: {BRAIN_URL}")
    print(f"  Storage: {STORAGE_PATH}")

    # Store config in app state for access by routes
    app.state.brain_url = BRAIN_URL
    app.state.template = TEMPLATE
    app.state.db_path = DB_PATH
    app.state.vector_path = VECTOR_PATH
    app.state.knowledge_path = KNOWLEDGE_PATH

    print("Intelligence service ready.")
    yield

    # Cleanup on shutdown
    print("Intelligence service shutting down.")


app = FastAPI(
    title="Nebulus Intelligence",
    description="Multi-source data intelligence with domain knowledge",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(data.router)
app.include_router(query.router)


@app.get("/")
def root():
    """Health check and service info."""
    return {
        "service": "nebulus-intelligence",
        "version": "0.1.0",
        "status": "running",
        "template": TEMPLATE,
        "brain_url": BRAIN_URL,
    }


@app.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the intelligence server."""
    uvicorn.run(
        "intelligence.server:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
    )


if __name__ == "__main__":
    main()
