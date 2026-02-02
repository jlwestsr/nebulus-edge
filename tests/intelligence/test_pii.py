"""Tests for the PII detection module."""

import pytest

from intelligence.core.pii import PIIDetector, PIIType


class TestPIIDetector:
    """Tests for PIIDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a PIIDetector instance."""
        return PIIDetector()

    def test_detect_ssn_with_dashes(self, detector):
        """Test SSN detection with dashes."""
        records = [{"ssn": "123-45-6789"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.SSN in report.pii_by_type
        assert report.pii_by_type[PIIType.SSN] == 1

    def test_detect_ssn_with_spaces(self, detector):
        """Test SSN detection with spaces."""
        records = [{"data": "SSN is 123 45 6789"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.SSN in report.pii_by_type

    def test_detect_phone_number(self, detector):
        """Test phone number detection."""
        records = [
            {"phone": "(555) 123-4567"},
            {"phone": "555-123-4567"},
            {"phone": "555.123.4567"},
        ]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.PHONE in report.pii_by_type
        assert report.pii_by_type[PIIType.PHONE] == 3

    def test_detect_email(self, detector):
        """Test email detection."""
        records = [{"email": "user@example.com"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.EMAIL in report.pii_by_type

    def test_detect_credit_card_visa(self, detector):
        """Test Visa credit card detection."""
        records = [{"card": "4111-1111-1111-1111"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.CREDIT_CARD in report.pii_by_type

    def test_detect_credit_card_mastercard(self, detector):
        """Test Mastercard detection."""
        records = [{"card": "5500 0000 0000 0004"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.CREDIT_CARD in report.pii_by_type

    def test_detect_ip_address(self, detector):
        """Test IP address detection."""
        records = [{"ip": "192.168.1.100"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.IP_ADDRESS in report.pii_by_type

    def test_detect_medical_record_number(self, detector):
        """Test MRN detection."""
        records = [{"mrn": "MRN: 12345678"}]
        report = detector.scan_records(records)

        assert report.has_pii
        assert PIIType.MEDICAL_RECORD in report.pii_by_type

    def test_no_pii_detected(self, detector):
        """Test when no PII is present."""
        records = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        report = detector.scan_records(records)

        assert not report.has_pii
        assert report.records_with_pii == 0

    def test_multiple_pii_types_in_record(self, detector):
        """Test detecting multiple PII types in same record."""
        records = [
            {
                "ssn": "123-45-6789",
                "email": "user@example.com",
                "phone": "555-123-4567",
            }
        ]
        report = detector.scan_records(records)

        assert report.has_pii
        assert len(report.pii_by_type) == 3
        assert PIIType.SSN in report.pii_by_type
        assert PIIType.EMAIL in report.pii_by_type
        assert PIIType.PHONE in report.pii_by_type

    def test_pii_columns_tracked(self, detector):
        """Test that PII columns are tracked."""
        records = [{"ssn_number": "123-45-6789", "email_addr": "user@example.com"}]
        report = detector.scan_records(records)

        assert "ssn_number" in report.pii_by_column
        assert "email_addr" in report.pii_by_column

    def test_column_name_hints(self, detector):
        """Test that column name hints generate warnings."""
        records = [{"social_security": "not-an-ssn"}]
        report = detector.scan_records(records)

        # Should warn about column name even if content doesn't match
        assert any("social_security" in w for w in report.warnings)


class TestPIIMasking:
    """Tests for PII masking functionality."""

    @pytest.fixture
    def detector(self):
        """Create a PIIDetector instance."""
        return PIIDetector()

    def test_mask_ssn(self, detector):
        """Test SSN masking."""
        records = [{"ssn": "123-45-6789"}]
        masked = detector.mask_records(records)

        assert masked[0]["ssn"] == "***-**-6789"

    def test_mask_phone(self, detector):
        """Test phone masking."""
        records = [{"phone": "555-123-4567"}]
        masked = detector.mask_records(records)

        assert masked[0]["phone"] == "***-***-4567"

    def test_mask_email(self, detector):
        """Test email masking."""
        records = [{"email": "john.doe@example.com"}]
        masked = detector.mask_records(records)

        assert "@example.com" in masked[0]["email"]
        assert "john.doe" not in masked[0]["email"]

    def test_mask_credit_card(self, detector):
        """Test credit card masking."""
        records = [{"card": "4111-1111-1111-1234"}]
        masked = detector.mask_records(records)

        assert masked[0]["card"] == "****-****-****-1234"

    def test_mask_ip_address(self, detector):
        """Test IP address masking."""
        records = [{"ip": "192.168.1.100"}]
        masked = detector.mask_records(records)

        assert masked[0]["ip"] == "192.168.1.***"

    def test_mask_preserves_non_pii(self, detector):
        """Test that non-PII data is preserved."""
        records = [{"name": "John", "ssn": "123-45-6789", "age": 30}]
        masked = detector.mask_records(records)

        assert masked[0]["name"] == "John"
        assert masked[0]["age"] == 30
        assert masked[0]["ssn"] == "***-**-6789"

    def test_mask_specific_columns(self, detector):
        """Test masking only specific columns."""
        records = [{"ssn": "123-45-6789", "email": "user@example.com"}]
        masked = detector.mask_records(records, columns=["ssn"])

        assert masked[0]["ssn"] == "***-**-6789"
        assert masked[0]["email"] == "user@example.com"  # Not masked


class TestPIISummary:
    """Tests for PII summary generation."""

    @pytest.fixture
    def detector(self):
        """Create a PIIDetector instance."""
        return PIIDetector()

    def test_summary_no_pii(self, detector):
        """Test summary when no PII detected."""
        records = [{"name": "John", "age": 30}]
        report = detector.scan_records(records)
        summary = detector.get_pii_summary(report)

        assert "No PII detected" in summary

    def test_summary_with_pii(self, detector):
        """Test summary with PII detected."""
        records = [
            {"ssn": "123-45-6789", "email": "user@example.com"},
            {"ssn": "987-65-4321", "email": "other@example.com"},
        ]
        report = detector.scan_records(records)
        summary = detector.get_pii_summary(report)

        assert "PII Detection Summary" in summary
        assert "Records with PII: 2" in summary
        assert "ssn" in summary.lower()
        assert "email" in summary.lower()


class TestSelectivePIIDetection:
    """Tests for selective PII type detection."""

    def test_detect_only_ssn(self):
        """Test detecting only SSN."""
        detector = PIIDetector(detect_types=[PIIType.SSN])
        records = [{"ssn": "123-45-6789", "email": "user@example.com"}]
        report = detector.scan_records(records)

        assert PIIType.SSN in report.pii_by_type
        assert PIIType.EMAIL not in report.pii_by_type

    def test_detect_only_email(self):
        """Test detecting only email."""
        detector = PIIDetector(detect_types=[PIIType.EMAIL])
        records = [{"ssn": "123-45-6789", "email": "user@example.com"}]
        report = detector.scan_records(records)

        assert PIIType.EMAIL in report.pii_by_type
        assert PIIType.SSN not in report.pii_by_type
