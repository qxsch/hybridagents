"""
Built-in privacy filters – import to make them available.
"""

from agents.privacy.filters.base import Filter
from agents.privacy.filters.email_filter import EmailFilter
from agents.privacy.filters.phone_filter import PhoneFilter
from agents.privacy.filters.iban_filter import IbanFilter
from agents.privacy.filters.tax_id_filter import TaxIdFilter
from agents.privacy.filters.credential_filter import CredentialFilter
from agents.privacy.filters.money_filter import MoneyFilter
from agents.privacy.filters.regex_filter import RegexFilter

# Registry of all built-in filter classes, keyed by their .name
BUILTIN_FILTERS: dict[str, type[Filter]] = {
    "email": EmailFilter,
    "phone": PhoneFilter,
    "iban": IbanFilter,
    "tax_id": TaxIdFilter,
    "credential": CredentialFilter,
    "money": MoneyFilter,
}


def get_builtin_filter(name: str) -> Filter | None:
    """Instantiate a built-in filter by name, or return None."""
    cls = BUILTIN_FILTERS.get(name)
    return cls() if cls else None


def all_builtin_names() -> list[str]:
    return list(BUILTIN_FILTERS.keys())


__all__ = [
    "Filter",
    "EmailFilter",
    "PhoneFilter",
    "IbanFilter",
    "TaxIdFilter",
    "CredentialFilter",
    "MoneyFilter",
    "RegexFilter",
    "BUILTIN_FILTERS",
    "get_builtin_filter",
    "all_builtin_names",
]
