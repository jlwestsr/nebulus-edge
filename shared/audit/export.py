"""Audit export and verification utilities for compliance reporting.

This module provides signed CSV export functionality for audit logs with tamper detection.
Exports include:
- CSV file with audit records
- HMAC-SHA256 signature file
- Metadata JSON with file hash and export details
"""

import csv
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from nebulus_core.intelligence.core.audit import AuditLogger


class AuditExporter:
    """Export and verify audit logs for compliance purposes.

    This class generates signed CSV exports of audit logs that include:
    - Tamper detection via SHA-256 file hashing
    - HMAC-SHA256 signatures for authenticity
    - Metadata for verification

    Example:
        exporter = AuditExporter(db_path="audit.db", secret_key="my-secret")
        exporter.export_csv(output_path="audit_export.csv", days=30)
        is_valid = exporter.verify_export(csv_path="audit_export.csv")
    """

    def __init__(self, db_path: str, secret_key: Optional[str] = None):
        """Initialize audit exporter.

        Args:
            db_path: Path to audit database
            secret_key: HMAC signing key (defaults to environment variable AUDIT_SECRET_KEY)
        """
        self.db_path = db_path
        self.secret_key = secret_key or os.getenv(
            "AUDIT_SECRET_KEY", "default-secret-change-in-production"
        )
        # Convert string to Path if needed
        db_path_obj = Path(db_path) if isinstance(db_path, str) else db_path
        self.audit_logger = AuditLogger(db_path=db_path_obj)

    def export_csv(
        self,
        output_path: str,
        days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Export audit logs to signed CSV.

        Args:
            output_path: Path to output CSV file
            days: Number of days to export (from now backwards)
            start_date: Start date for export range
            end_date: End date for export range

        Returns:
            Dict with paths to generated files (csv, signature, metadata)

        Raises:
            ValueError: If neither days nor start_date/end_date are provided
        """
        # Determine date range
        if days is not None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        elif start_date is None or end_date is None:
            raise ValueError("Must provide either 'days' or 'start_date'/'end_date'")

        # Query audit events
        events = self.audit_logger.get_events(
            start_time=start_date,
            end_time=end_date,
            limit=999999,  # Export all matching records (large number)
        )

        # Write CSV
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="") as f:
            if not events:
                # Write empty CSV with headers
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "event_type",
                        "user_id",
                        "session_id",
                        "ip_address",
                        "resource",
                        "action",
                        "details",
                        "success",
                        "error_message",
                    ]
                )
            else:
                # Write events
                fieldnames = [
                    "timestamp",
                    "event_type",
                    "user_id",
                    "session_id",
                    "ip_address",
                    "resource",
                    "action",
                    "details",
                    "success",
                    "error_message",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for event in events:
                    writer.writerow(
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "event_type": event.event_type.value,
                            "user_id": event.user_id,
                            "session_id": event.session_id or "",
                            "ip_address": event.ip_address or "",
                            "resource": event.resource or "",
                            "action": event.action or "",
                            "details": event.details or "",
                            "success": event.success,
                            "error_message": event.error_message or "",
                        }
                    )

        # Generate signature and metadata
        csv_hash = self._hash_file(output_file)
        signature = self._sign_file(output_file)

        # Write signature file
        sig_file = output_file.with_suffix(output_file.suffix + ".sig")
        with open(sig_file, "w") as f:
            f.write(signature)

        # Write metadata file
        meta_file = output_file.with_suffix(output_file.suffix + ".meta.json")
        metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "record_count": len(events),
            "csv_hash": csv_hash,
            "signature_algorithm": "HMAC-SHA256",
        }
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "csv": str(output_file),
            "signature": str(sig_file),
            "metadata": str(meta_file),
        }

    def verify_export(self, csv_path: str) -> Dict[str, bool]:
        """Verify integrity and authenticity of exported CSV.

        Args:
            csv_path: Path to CSV file to verify

        Returns:
            Dict with verification results (hash_valid, signature_valid, tampered)
        """
        csv_file = Path(csv_path)
        sig_file = csv_file.with_suffix(csv_file.suffix + ".sig")
        meta_file = csv_file.with_suffix(csv_file.suffix + ".meta.json")

        # Check files exist
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        if not sig_file.exists():
            raise FileNotFoundError(f"Signature file not found: {sig_file}")
        if not meta_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_file}")

        # Load metadata
        with open(meta_file) as f:
            metadata = json.load(f)

        # Verify file hash
        current_hash = self._hash_file(csv_file)
        hash_valid = current_hash == metadata["csv_hash"]

        # Verify signature
        with open(sig_file) as f:
            stored_signature = f.read().strip()
        current_signature = self._sign_file(csv_file)
        signature_valid = hmac.compare_digest(current_signature, stored_signature)

        # Overall tamper detection
        tampered = not (hash_valid and signature_valid)

        return {
            "hash_valid": hash_valid,
            "signature_valid": signature_valid,
            "tampered": tampered,
            "record_count": metadata["record_count"],
            "export_date": metadata["export_timestamp"],
        }

    def _hash_file(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file.

        Args:
            file_path: Path to file to hash

        Returns:
            Hexadecimal digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _sign_file(self, file_path: Path) -> str:
        """Generate HMAC-SHA256 signature for file.

        Args:
            file_path: Path to file to sign

        Returns:
            Hexadecimal digest of HMAC signature
        """
        h = hmac.new(self.secret_key.encode(), digestmod=hashlib.sha256)
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
