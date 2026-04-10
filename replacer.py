"""Apply approved replacements consistently throughout a document."""
import re


def build_mapping(approved: list[dict]) -> dict[str, str]:
    """Build a {original: replacement} mapping from approved entities."""
    return {e["tekst"]: e["vervanging"] for e in approved}


def apply(text: str, mapping: dict[str, str]) -> str:
    """Apply all replacements to the text.

    Longer matches first to avoid partial replacements.
    Case-insensitive: 'Leidse regio' matches 'Leidse Regio' key in standaard.yaml.
    Lambda replacement avoids re.sub interpreting backslashes in replacement strings.
    """
    for original in sorted(mapping.keys(), key=len, reverse=True):
        replacement = mapping[original]
        text = re.sub(
            re.escape(original),
            lambda m, r=replacement: r,
            text,
            flags=re.IGNORECASE,
        )
    return text
