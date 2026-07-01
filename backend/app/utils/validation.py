import re
from typing import Any

from app.core.exceptions import ValidationException


def validate_non_empty(value: Any, field_name: str) -> None:
    """
    Validate that a given string or object value is non-empty.
    """
    if not value:
        raise ValidationException(f"Validation failure: '{field_name}' parameter cannot be empty.")
    if isinstance(value, str) and not value.strip():
        raise ValidationException(f"Validation failure: '{field_name}' parameter cannot be blank.")

def validate_phone_number(phone: str) -> None:
    """
    Validate that a phone number matches standard formats (+E.164, etc.).
    """
    # Quick regex pattern matching E.164 formatting
    pattern = r"^\+?[1-9]\d{1,14}$"
    if not re.match(pattern, phone):
        raise ValidationException(
            f"Validation failure: Phone number '{phone}' is invalid (does not match E.164 specification)."
        )
