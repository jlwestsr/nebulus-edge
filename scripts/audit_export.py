#!/usr/bin/env python3
"""CLI utility for exporting and verifying audit logs.

Usage:
    # Export last 30 days
    python scripts/audit_export.py export \\
        --db-path intelligence/storage/audit/audit.db \\
        --output /var/backups/audit_20260206.csv \\
        --days 30

    # Verify exported CSV
    python scripts/audit_export.py verify \\
        --csv /var/backups/audit_20260206.csv
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.audit.export import AuditExporter  # noqa: E402


def export_command(args):
    """Export audit logs to signed CSV."""
    exporter = AuditExporter(db_path=args.db_path)

    print(f"Exporting audit logs from: {args.db_path}")
    print(f"Output: {args.output}")
    print(f"Days: {args.days}")

    files = exporter.export_csv(output_path=args.output, days=args.days)

    print("\n✓ Export completed successfully!")
    print(f"  CSV: {files['csv']}")
    print(f"  Signature: {files['signature']}")
    print(f"  Metadata: {files['metadata']}")


def verify_command(args):
    """Verify exported CSV integrity and authenticity."""
    # Extract db_path from args if provided, otherwise derive from CSV path
    if hasattr(args, "db_path") and args.db_path:
        db_path = args.db_path
    else:
        # Try to infer from CSV path (assume same directory structure)
        csv_path = Path(args.csv)
        if "intelligence" in str(csv_path):
            db_path = "intelligence/storage/audit/audit.db"
        elif "brain" in str(csv_path):
            db_path = "brain/audit/audit.db"
        else:
            print("Error: Cannot infer database path. Please provide --db-path")
            sys.exit(1)

    exporter = AuditExporter(db_path=db_path)

    print(f"Verifying: {args.csv}")

    try:
        result = exporter.verify_export(csv_path=args.csv)

        print("\nVerification Results:")
        print(f"  Hash valid: {result['hash_valid']}")
        print(f"  Signature valid: {result['signature_valid']}")
        print(f"  Record count: {result['record_count']}")
        print(f"  Export date: {result['export_date']}")

        if result["tampered"]:
            print("\n⚠ WARNING: File has been tampered with!")
            sys.exit(1)
        else:
            print("\n✓ File integrity verified - no tampering detected")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Audit log export and verification utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export audit logs to CSV")
    export_parser.add_argument("--db-path", required=True, help="Path to audit database")
    export_parser.add_argument("--output", required=True, help="Output CSV file path")
    export_parser.add_argument(
        "--days", type=int, default=30, help="Number of days to export (default: 30)"
    )

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify exported CSV")
    verify_parser.add_argument("--csv", required=True, help="Path to CSV file to verify")
    verify_parser.add_argument("--db-path", help="Path to audit database (optional)")

    args = parser.parse_args()

    if args.command == "export":
        export_command(args)
    elif args.command == "verify":
        verify_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
