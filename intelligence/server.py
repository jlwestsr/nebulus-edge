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

from intelligence.api import data, feedback, insights, knowledge, query
from nebulus_core.intelligence.core.audit import AuditLogger
from nebulus_core.llm.client import LLMClient
from nebulus_core.vector.client import VectorClient
from shared.config.audit_config import AuditConfig
from shared.middleware.audit_middleware import AuditMiddleware

# Configuration
BRAIN_URL = os.getenv("BRAIN_URL", "http://localhost:8080")
TEMPLATE = os.getenv("INTELLIGENCE_TEMPLATE", "dealership")
MODEL = os.getenv("NEBULUS_MODEL", "default")
STORAGE_PATH = Path(__file__).parent / "storage"
DB_PATH = STORAGE_PATH / "databases"
VECTOR_PATH = STORAGE_PATH / "vectors"
KNOWLEDGE_PATH = STORAGE_PATH / "knowledge"
FEEDBACK_PATH = STORAGE_PATH / "feedback"
AUDIT_PATH = STORAGE_PATH / "audit"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup, cleanup on shutdown."""
    # Ensure storage directories exist
    DB_PATH.mkdir(parents=True, exist_ok=True)
    VECTOR_PATH.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_PATH.mkdir(parents=True, exist_ok=True)
    FEEDBACK_PATH.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.mkdir(parents=True, exist_ok=True)

    print("Intelligence service starting...")
    print(f"  Template: {TEMPLATE}")
    print(f"  Brain URL: {BRAIN_URL}")
    print(f"  Storage: {STORAGE_PATH}")

    # Initialize audit logging
    audit_config = AuditConfig.from_env()
    audit_db_path = AUDIT_PATH / "audit.db"
    audit_logger = AuditLogger(db_path=audit_db_path)

    print(f"  Audit logging: {'enabled' if audit_config.enabled else 'disabled'}")
    print(f"  Audit retention: {audit_config.retention_days} days")

    # Store config in app state for access by routes
    app.state.template = TEMPLATE
    app.state.db_path = DB_PATH
    app.state.vector_path = VECTOR_PATH
    app.state.knowledge_path = KNOWLEDGE_PATH
    app.state.feedback_path = FEEDBACK_PATH
    app.state.audit_logger = audit_logger
    app.state.audit_config = audit_config

    # Create shared core clients
    app.state.llm = LLMClient(base_url=BRAIN_URL)
    app.state.vector_client = VectorClient(
        settings={"mode": "embedded", "path": str(VECTOR_PATH)}
    )
    app.state.model = MODEL

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

# Add audit middleware
audit_config = AuditConfig.from_env()
app.add_middleware(
    AuditMiddleware,
    enabled=audit_config.enabled,
    debug=audit_config.debug,
    default_user="appliance-admin",
)

# Register routers
app.include_router(data.router)
app.include_router(query.router)
app.include_router(knowledge.router)
app.include_router(feedback.router)
app.include_router(insights.router)


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
    reload = os.getenv("INTELLIGENCE_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "intelligence.server:app",
        host="0.0.0.0",
        port=8081,
        reload=reload,
    )


if __name__ == "__main__":
    main()
