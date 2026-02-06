"""Audit logging configuration for Nebulus Edge services."""

import os
from pydantic import BaseModel, Field


class AuditConfig(BaseModel):
    """Configuration for audit logging.

    Attributes:
        enabled: Enable/disable audit logging
        retention_days: Number of days to retain audit logs (default: 2555 = 7 years for HIPAA)
        debug: Enable debug mode to log full request/response bodies (DEVELOPMENT ONLY)
    """

    enabled: bool = Field(default=True)
    retention_days: int = Field(default=2555)
    debug: bool = Field(default=False)

    @classmethod
    def from_env(cls) -> "AuditConfig":
        """Load audit configuration from environment variables."""
        return cls(
            enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
            retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "2555")),
            debug=os.getenv("AUDIT_DEBUG", "false").lower() == "true",
        )
