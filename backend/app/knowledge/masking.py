from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass
class MaskResult:
    text: str
    categories: set[str] = field(default_factory=set)


# Regex patterns for Chinese PII
_PHONE_PATTERN = re.compile(r"(\+?86[-\s]?)?1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}")
_IDENTITY_PATTERN = re.compile(
    r"[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
)
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _mask_phone(text: str) -> str:
    """Mask phone numbers: 13812345678 -> 138****5678"""

    def _replacer(m: re.Match) -> str:
        digits = re.sub(r"[^\d]", "", m.group())
        if len(digits) == 11:
            return digits[:3] + "****" + digits[-4:]
        return "***"

    return _PHONE_PATTERN.sub(_replacer, text)


def _mask_identity(text: str) -> str:
    """Mask identity numbers: 530102199001011234 -> 530102********1234"""

    def _replacer(m: re.Match) -> str:
        digits = m.group()
        return digits[:6] + "********" + digits[-4:]

    return _IDENTITY_PATTERN.sub(_replacer, text)


def _mask_email(text: str) -> str:
    """Mask email addresses: user@example.com -> u**r@example.com"""

    def _replacer(m: re.Match) -> str:
        email = m.group()
        at_idx = email.index("@")
        local = email[:at_idx]
        if len(local) <= 2:
            masked_local = local[0] + "**"
        else:
            masked_local = local[0] + "**" + local[-1]
        return masked_local + email[at_idx:]

    return _EMAIL_PATTERN.sub(_replacer, text)


def _mask_addresses(text: str, address_patterns: Sequence[str] | None) -> str:
    """Mask addresses matched by configured business-specific patterns."""
    if not address_patterns:
        return text
    result = text
    for pattern in address_patterns:
        result = re.sub(pattern, "[地址已脱敏]", result)
    return result


def _has_address(text: str, address_patterns: Sequence[str] | None) -> bool:
    if not address_patterns:
        return False
    return any(re.search(pattern, text) for pattern in address_patterns)


def mask_sensitive_text(
    text: str,
    address_patterns: Sequence[str] | None = None,
) -> MaskResult:
    """Apply all masking rules and return the result with detected categories."""
    categories: set[str] = set()

    if _PHONE_PATTERN.search(text):
        categories.add("phone")
    if _IDENTITY_PATTERN.search(text):
        categories.add("identity_number")
    if _EMAIL_PATTERN.search(text):
        categories.add("email")
    if _has_address(text, address_patterns):
        categories.add("address")

    result = text
    result = _mask_phone(result)
    result = _mask_identity(result)
    result = _mask_email(result)
    result = _mask_addresses(result, address_patterns)

    return MaskResult(text=result, categories=categories)


def safe_knowledge_log_fields(
    text: str,
    address_patterns: Sequence[str] | None = None,
) -> dict[str, object]:
    """Return log-safe knowledge preprocessing fields without raw source text."""
    masked = mask_sensitive_text(text, address_patterns=address_patterns)
    return {
        "masked_text": masked.text,
        "sensitive_categories": sorted(masked.categories),
    }
