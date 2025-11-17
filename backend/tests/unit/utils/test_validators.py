"""Unit tests for validators utility module."""
from datetime import date
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from src.utils.validators import (
    validate_email,
    validate_password,
    validate_uuid,
    validate_date_range,
    validate_positive_number,
    validate_enum_value,
    validate_pagination_params,
    validate_json_structure,
    sanitize_string,
)


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test validation of valid email addresses."""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user+tag@domain.co.uk") == "test.user+tag@domain.co.uk"
        assert validate_email("UPPERCASE@EXAMPLE.COM") == "uppercase@example.com"

    def test_email_normalization(self):
        """Test email normalization (lowercase, trim)."""
        assert validate_email("  User@Example.Com  ") == "user@example.com"
        assert validate_email("Test@DOMAIN.com") == "test@domain.com"

    def test_invalid_email_formats(self):
        """Test rejection of invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user name@example.com",
            "",
        ]

        for email in invalid_emails:
            with pytest.raises(HTTPException) as exc_info:
                validate_email(email)
            assert exc_info.value.status_code == 400
            assert "INVALID_EMAIL" in str(exc_info.value.detail)


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_passwords(self):
        """Test validation of strong passwords."""
        valid_passwords = [
            "SecurePass123!",
            "MyPassword1",
            "Another1Valid",
            "Str0ngP@ssw0rd",
        ]

        for password in valid_passwords:
            validate_password(password)  # Should not raise

    def test_password_too_short(self):
        """Test rejection of passwords under 8 characters."""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("Short1")
        assert exc_info.value.status_code == 400
        assert "WEAK_PASSWORD" in str(exc_info.value.detail)
        assert "8 characters" in str(exc_info.value.detail)

    def test_password_no_uppercase(self):
        """Test rejection of passwords without uppercase letter."""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("lowercase123")
        assert exc_info.value.status_code == 400
        assert "WEAK_PASSWORD" in str(exc_info.value.detail)
        assert "uppercase" in str(exc_info.value.detail)

    def test_password_no_lowercase(self):
        """Test rejection of passwords without lowercase letter."""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("UPPERCASE123")
        assert exc_info.value.status_code == 400
        assert "WEAK_PASSWORD" in str(exc_info.value.detail)
        assert "lowercase" in str(exc_info.value.detail)

    def test_password_no_digit(self):
        """Test rejection of passwords without digit."""
        with pytest.raises(HTTPException) as exc_info:
            validate_password("NoDigitsHere")
        assert exc_info.value.status_code == 400
        assert "WEAK_PASSWORD" in str(exc_info.value.detail)
        assert "digit" in str(exc_info.value.detail)


class TestValidateUUID:
    """Tests for UUID validation."""

    def test_valid_uuid(self):
        """Test validation of valid UUID strings."""
        test_uuid = uuid4()
        result = validate_uuid(str(test_uuid))
        assert result == test_uuid
        assert isinstance(result, UUID)

    def test_valid_uuid_formats(self):
        """Test various valid UUID formats."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        ]

        for uuid_str in valid_uuids:
            result = validate_uuid(uuid_str)
            assert str(result) == uuid_str

    def test_invalid_uuid_formats(self):
        """Test rejection of invalid UUID formats."""
        invalid_uuids = [
            "not-a-uuid",
            "123-456-789",
            "550e8400-e29b-41d4-a716-44665544000",  # Too short
            "550e8400-e29b-41d4-a716-4466554400001",  # Too long
            "",
        ]

        for uuid_str in invalid_uuids:
            with pytest.raises(HTTPException) as exc_info:
                validate_uuid(uuid_str)
            assert exc_info.value.status_code == 400
            assert "INVALID_UUID" in str(exc_info.value.detail)


class TestValidateDateRange:
    """Tests for date range validation."""

    def test_valid_date_range(self):
        """Test validation of valid date ranges."""
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)
        validate_date_range(start, end)  # Should not raise

    def test_same_day_range_invalid(self):
        """Test rejection when start and end are same day."""
        same_date = date(2025, 6, 15)
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range(same_date, same_date)
        assert exc_info.value.status_code == 400
        assert "INVALID_DATE_RANGE" in str(exc_info.value.detail)

    def test_reversed_date_range(self):
        """Test rejection when end date is before start date."""
        start = date(2025, 12, 31)
        end = date(2025, 1, 1)
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range(start, end)
        assert exc_info.value.status_code == 400
        assert "INVALID_DATE_RANGE" in str(exc_info.value.detail)


class TestValidatePositiveNumber:
    """Tests for positive number validation."""

    def test_valid_positive_numbers(self):
        """Test validation of positive numbers."""
        validate_positive_number(1)
        validate_positive_number(100)
        validate_positive_number(0.5)
        validate_positive_number(1.0, "price")

    def test_zero_is_invalid(self):
        """Test rejection of zero."""
        with pytest.raises(HTTPException) as exc_info:
            validate_positive_number(0)
        assert exc_info.value.status_code == 400
        assert "INVALID_VALUE" in str(exc_info.value.detail)

    def test_negative_numbers_invalid(self):
        """Test rejection of negative numbers."""
        with pytest.raises(HTTPException) as exc_info:
            validate_positive_number(-1)
        assert exc_info.value.status_code == 400
        assert "INVALID_VALUE" in str(exc_info.value.detail)

        with pytest.raises(HTTPException) as exc_info:
            validate_positive_number(-0.5, "amount")
        assert exc_info.value.status_code == 400
        assert "amount" in str(exc_info.value.detail)


class TestValidateEnumValue:
    """Tests for enum value validation."""

    def test_valid_enum_values(self):
        """Test validation of values in allowed set."""
        allowed = ["red", "green", "blue"]
        validate_enum_value("red", allowed)
        validate_enum_value("green", allowed, "color")

    def test_invalid_enum_value(self):
        """Test rejection of values not in allowed set."""
        allowed = ["small", "medium", "large"]
        with pytest.raises(HTTPException) as exc_info:
            validate_enum_value("extra-large", allowed, "size")
        assert exc_info.value.status_code == 400
        assert "INVALID_VALUE" in str(exc_info.value.detail)
        assert "size" in str(exc_info.value.detail)
        assert "small, medium, large" in str(exc_info.value.detail)


class TestValidatePaginationParams:
    """Tests for pagination parameter validation."""

    def test_valid_pagination_params(self):
        """Test validation of valid pagination parameters."""
        skip, limit = validate_pagination_params(1, 20)
        assert skip == 0
        assert limit == 20

        skip, limit = validate_pagination_params(2, 50)
        assert skip == 50
        assert limit == 50

        skip, limit = validate_pagination_params(5, 10)
        assert skip == 40
        assert limit == 10

    def test_default_pagination_params(self):
        """Test default pagination parameters."""
        skip, limit = validate_pagination_params()
        assert skip == 0
        assert limit == 20

    def test_page_below_one(self):
        """Test rejection of page number < 1."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination_params(page=0)
        assert exc_info.value.status_code == 400
        assert "INVALID_PAGINATION" in str(exc_info.value.detail)

        with pytest.raises(HTTPException) as exc_info:
            validate_pagination_params(page=-1)
        assert exc_info.value.status_code == 400

    def test_page_size_limits(self):
        """Test rejection of page_size outside 1-100 range."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination_params(page=1, page_size=0)
        assert exc_info.value.status_code == 400
        assert "INVALID_PAGINATION" in str(exc_info.value.detail)

        with pytest.raises(HTTPException) as exc_info:
            validate_pagination_params(page=1, page_size=101)
        assert exc_info.value.status_code == 400
        assert "INVALID_PAGINATION" in str(exc_info.value.detail)

    def test_boundary_page_sizes(self):
        """Test boundary page sizes (1 and 100)."""
        skip, limit = validate_pagination_params(page=1, page_size=1)
        assert limit == 1

        skip, limit = validate_pagination_params(page=1, page_size=100)
        assert limit == 100


class TestValidateJsonStructure:
    """Tests for JSON structure validation."""

    def test_valid_json_with_all_fields(self):
        """Test validation of JSON with all required fields."""
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        validate_json_structure(data, ["name", "age", "email"])  # Should not raise

    def test_valid_json_with_extra_fields(self):
        """Test validation allows extra fields beyond required."""
        data = {"name": "John", "age": 30, "extra": "data"}
        validate_json_structure(data, ["name", "age"])  # Should not raise

    def test_missing_required_fields(self):
        """Test rejection when required fields are missing."""
        data = {"name": "John"}
        with pytest.raises(HTTPException) as exc_info:
            validate_json_structure(data, ["name", "age", "email"])
        assert exc_info.value.status_code == 400
        assert "MISSING_FIELDS" in str(exc_info.value.detail)
        assert "age" in str(exc_info.value.detail)
        assert "email" in str(exc_info.value.detail)

    def test_non_dict_data(self):
        """Test rejection of non-dict data."""
        with pytest.raises(HTTPException) as exc_info:
            validate_json_structure(["not", "a", "dict"], ["field"])
        assert exc_info.value.status_code == 400
        assert "INVALID_JSON" in str(exc_info.value.detail)

        with pytest.raises(HTTPException) as exc_info:
            validate_json_structure("string", ["field"])
        assert exc_info.value.status_code == 400


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_trim_whitespace(self):
        """Test removal of leading/trailing whitespace."""
        assert sanitize_string("  hello  ") == "hello"
        assert sanitize_string("\t\ntest\n\t") == "test"

    def test_string_within_max_length(self):
        """Test strings within max_length pass validation."""
        result = sanitize_string("hello", max_length=10)
        assert result == "hello"

        result = sanitize_string("exactly10c", max_length=10)
        assert result == "exactly10c"

    def test_string_exceeds_max_length(self):
        """Test rejection of strings exceeding max_length."""
        with pytest.raises(HTTPException) as exc_info:
            sanitize_string("this is too long", max_length=10)
        assert exc_info.value.status_code == 400
        assert "STRING_TOO_LONG" in str(exc_info.value.detail)
        assert "10" in str(exc_info.value.detail)

    def test_no_max_length(self):
        """Test sanitization without max_length constraint."""
        long_string = "a" * 1000
        result = sanitize_string(long_string)
        assert result == long_string

    def test_empty_string(self):
        """Test handling of empty strings."""
        assert sanitize_string("") == ""
        assert sanitize_string("   ") == ""
