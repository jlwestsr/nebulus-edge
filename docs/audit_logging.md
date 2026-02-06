# Audit Logging

Nebulus Edge implements comprehensive audit logging for HIPAA compliance and security monitoring.

## Overview

**Why**: Medical practices, law firms, and accountants require audit trails to prove PHI/PII was not accessed inappropriately. This is a legal requirement for HIPAA compliance and Business Associate Agreements (BAA).

**Architecture**: Hybrid middleware + dependency injection pattern
- **Middleware**: Automatically enriches all requests with audit context (user_id, session_id, IP, SHA-256 hashes)
- **Route logging**: Explicit business-level audit events (data uploads, queries, deletions)

## Configuration

Environment variables (set in `infrastructure/pm2_config.json`):

```bash
AUDIT_ENABLED=true              # Enable/disable audit logging
AUDIT_RETENTION_DAYS=2555       # 7 years for HIPAA (default)
AUDIT_DEBUG=false               # Log full request/response bodies (DEVELOPMENT ONLY)
```

## What Gets Logged

### Brain Service (LLM Inference)

| Route | Event Type | Details Logged |
|-------|-----------|---------------|
| `/v1/chat/completions` | `QUERY_NATURAL` | model, message_count, prompt_length, response_length, max_tokens, temperature, duration_ms, request_hash, response_hash |
| `/v1/models` | `DATA_VIEW` | action="list_models" |

### Intelligence Service (Data Analytics)

| Route | Event Type | Details Logged |
|-------|-----------|---------------|
| `/data/upload` | `DATA_UPLOAD` | rows_imported, columns, pii_detected, records_embedded, request_hash, response_hash |
| `/data/upload` (if PII) | `PII_DETECTED` | pii_types, records_affected, columns_with_pii |
| `/data/tables/{id}` DELETE | `DATA_DELETE` | table_name |
| `/query/ask` | `QUERY_NATURAL` | question_hash, classification, sql_used, rows_returned |
| `/query/sql` | `QUERY_SQL` | sql_hash, rows_returned, success/error |
| `/query/similar` | `QUERY_SEMANTIC` | query_hash, table_name, rows_returned |

## Storage Locations

```
brain/audit/audit.db                       # Brain service audit logs
intelligence/storage/audit/audit.db        # Intelligence service audit logs
```

## SHA-256 Hashing Strategy

**Purpose**: Verify request/response integrity without storing sensitive data

**How it works**:
1. Middleware computes SHA-256 of full request body → stored as `request_hash`
2. Middleware computes SHA-256 of full response body → stored as `response_hash`
3. Hashes are included in audit log `details` JSON field
4. Full bodies are NOT stored (unless `AUDIT_DEBUG=true`)

**Verification**: Compare hash of current request/response with logged hash to detect tampering

## Compliance Export

Export audit logs for compliance reporting:

```bash
# Export last 30 days
python scripts/audit_export.py export \
  --db-path intelligence/storage/audit/audit.db \
  --output /var/backups/audit_20260206.csv \
  --days 30

# Verify exported CSV
python scripts/audit_export.py verify \
  --csv /var/backups/audit_20260206.csv
```

**Export artifacts**:
- `audit_20260206.csv` - Audit records in CSV format
- `audit_20260206.csv.sig` - HMAC-SHA256 signature
- `audit_20260206.csv.meta.json` - Export metadata (timestamp, record count, file hash)

**Verification checks**:
- CSV hash matches metadata
- HMAC signature is valid
- Reports tampering if either fails

## User/Session Tracking

**Open WebUI integration**:
- Extracts `X-User-ID` header (user email from Open WebUI)
- Extracts `X-Session-ID` header (conversation ID)
- Falls back to `"appliance-admin"` if headers missing

**Single-appliance mode**:
- Default user_id: `"appliance-admin"` (no multi-user support yet)
- Session tracking: UUID per conversation thread
- IP tracking: Always captured (useful for remote access audits)

## Performance Impact

**Measured overhead per request**:
- Middleware context setup: 2-5ms (UUID, header parsing)
- SHA-256 hashing: 1-2ms (typical <100KB bodies)
- SQLite insert: 1-2ms (indexed, non-blocking)
- **Total: <10ms** (meets requirement)

**Optimization strategies**:
- FastAPI handles SQLite writes in threadpool (non-blocking)
- AuditLogger reuses connections via context managers
- Health check routes excluded from audit

## Security Considerations

**Threats mitigated**:
- Unauthorized data access (all queries logged with user/IP)
- Data tampering (SHA-256 hashes detect modifications)
- Export forgery (HMAC signatures prevent fake reports)
- PII exposure (full bodies not logged by default)

**Threats NOT mitigated** (future hardening):
- Insider attacks with audit DB access (need OS-level controls)
- Database-level tampering (need write-once storage)
- Key compromise (HMAC key stored in application memory)

**Production hardening** (Phase 2):
- Secure key management (HashiCorp Vault, AWS KMS)
- Key rotation
- Access control on audit endpoints
- Encrypted audit database at rest

## Testing

Unit tests:
```bash
pytest tests/test_audit_middleware.py  # Middleware context enrichment
pytest tests/test_audit_export.py      # Export/verification functionality
```

Integration tests:
```bash
pytest tests/integration/test_intelligence_audit.py  # End-to-end audit flow
```

## Implementation Details

**Code locations**:
- Middleware: `shared/middleware/audit_middleware.py`
- Configuration: `shared/config/audit_config.py`
- Export utility: `shared/audit/export.py`
- CLI tool: `scripts/audit_export.py`
- Intelligence API integration: `intelligence/api/data.py`, `intelligence/api/query.py`
- Brain API integration: `brain/server.py`

**Dependencies**:
- `nebulus_core.intelligence.core.audit` - AuditLogger, AuditEvent, AuditEventType
- SQLite (built-in to Python 3.10+)
- FastAPI middleware system
