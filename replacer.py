"""Apply approved replacements consistently throughout a document."""


def build_mapping(approved: list[dict]) -> dict[str, str]:
    """Build a {original: replacement} mapping from approved entities."""
    return {e["tekst"]: e["vervanging"] for e in approved}


def apply(text: str, mapping: dict[str, str]) -> str:
    """Apply all replacements to the text. Longer matches first to avoid partial replacements."""
    # Sort by length descending so longer strings are replaced before substrings
    for original in sorted(mapping.keys(), key=len, reverse=True):
        replacement = mapping[original]
        text = text.replace(original, replacement)
    return text
