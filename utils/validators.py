import re

def validate_phone(phone):
    """
    Validates that a phone number is either:
    1. Exactly 10 digits (digits only)
    2. Starts with '+' followed by 1 to 4 digits country code, followed by exactly 10 digits
    """
    if not phone:
        return False
    if phone.isdigit() and len(phone) == 10:
        return True
    if phone.startswith('+') and phone[1:].isdigit():
        # Minimum: + (1) + country_code (1) + number (10) = 12 chars
        # Maximum: + (1) + country_code (4) + number (10) = 15 chars
        if 12 <= len(phone) <= 15:
            return True
    return False

def split_phone(phone):
    """
    Splits a phone number into (country_code, local_number).
    If it doesn't start with '+', returns ('+91', phone).
    """
    if not phone:
        return '+91', ''
    if phone.startswith('+'):
        if len(phone) >= 11:
            return phone[:-10], phone[-10:]
    return '+91', phone
