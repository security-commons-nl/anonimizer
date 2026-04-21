"""Apply approved replacements consistently throughout a document.

Word-boundary logica: voor korte keys (≤4 tekens) of keys die geheel uit
letters/cijfers bestaan (bv. "BIO", "FG", "IB&P") wrappen we de match met
regex word-boundaries zodat de key niet binnen een langer woord matcht
(bv. "BIO" in "biography"). Voor langere frasen is dit niet nodig en kan
het zelfs fout gaan bij frasen die op een niet-woord-karakter eindigen.
"""
import re


KORTE_KEY_DREMPEL = 4


def _is_korte_key(key: str) -> bool:
    """Bepaal of een key word-boundary bescherming nodig heeft.

    True als:
      - Key is ≤ KORTE_KEY_DREMPEL tekens, EN
      - Key begint én eindigt met een woord-karakter (letter/cijfer/_)

    Keys met speciale tekens (&, -, @, spaties) krijgen geen \\b omdat
    dat regex-semantisch niet betrouwbaar is aan de grens.
    """
    if len(key) > KORTE_KEY_DREMPEL:
        return False
    if not key:
        return False
    return bool(re.match(r"\w", key[0])) and bool(re.match(r"\w", key[-1]))


def build_mapping(approved: list[dict]) -> dict[str, str]:
    """Build a {original: replacement} mapping from approved entities."""
    return {e["tekst"]: e["vervanging"] for e in approved}


def apply(text: str, mapping: dict[str, str]) -> str:
    """Apply all replacements to the text.

    Longer matches first to avoid partial replacements.
    Case-insensitive: 'Leidse regio' matches 'Leidse Regio' key.
    Korte woord-keys (≤4 tekens, alfanumeriek) krijgen \\b-wrapping zodat
    'FG' niet binnen 'FGV' matcht.
    Lambda replacement avoids re.sub interpreting backslashes.
    """
    for original in sorted(mapping.keys(), key=len, reverse=True):
        replacement = mapping[original]
        patroon = re.escape(original)
        if _is_korte_key(original):
            patroon = r"\b" + patroon + r"\b"
        text = re.sub(
            patroon,
            lambda m, r=replacement: r,
            text,
            flags=re.IGNORECASE,
        )
    return text
