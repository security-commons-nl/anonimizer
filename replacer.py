"""Apply approved replacements consistently throughout a document.

Word-boundary logica: elke key waarvan het eerste én laatste teken een
woord-karakter is (letter/cijfer/_) krijgt `\\b`-wrapping. Dat voorkomt
dat 'beveiliging' matcht binnen 'informatiebeveiliging' of 'Leiden'
binnen 'begeleiden'. Keys die beginnen of eindigen op niet-woord-tekens
(bv. '(C)ISO', 'IB-') krijgen geen \\b omdat dat regex-semantisch niet
betrouwbaar is aan de grens.

Post-processing: direct op elkaar volgende lidwoorden ("de de", "het
het", "een een") worden gecollapsed. Dit fixt het geval waarin de bron-
tekst al een lidwoord bevat en de vervanging er ook een meeneemt.
"""
import re


# Behouden voor backwards-compat met bestaande tests; niet meer actief
# gebruikt in apply().
KORTE_KEY_DREMPEL = 4


def _heeft_word_grens(key: str) -> bool:
    """True als de key op een woord-karakter begint én eindigt.

    Alleen dan is `\\b`-wrapping veilig en zinvol — bij keys die op een
    niet-woord-karakter eindigen (bv. 'IB-') match `\\b` niet zoals je
    zou verwachten.
    """
    if not key:
        return False
    return bool(re.match(r"\w", key[0])) and bool(re.match(r"\w", key[-1]))


def _is_korte_key(key: str) -> bool:
    """Backwards-compat shim voor bestaande tests. Zie _heeft_word_grens."""
    if len(key) > KORTE_KEY_DREMPEL:
        return False
    return _heeft_word_grens(key)


# Collapse patterns voor dubbele lidwoorden. Case-insensitive. De
# vervanger gebruikt het eerste woord (met originele hoofdletter) zodat
# 'De de CISO' → 'De CISO' wordt en 'de De CISO' → 'de CISO'.
_DUBBEL_LIDWOORD = re.compile(
    r"\b(de|het|een)\s+(?:de|het|een)\s+",
    flags=re.IGNORECASE,
)


def _collapse_dubbele_lidwoorden(text: str) -> str:
    return _DUBBEL_LIDWOORD.sub(lambda m: m.group(1) + " ", text)


# Post-replacement collapse: een lijst van 2+ identieke VOORBEELDGEMEENTE-
# tokens (komma-gescheiden, 'en', 'of') wordt teruggebracht naar 'de
# betrokken gemeenten'. Zonder deze stap zie je constructies als
# 'VOORBEELDGEMEENTE, VOORBEELDGEMEENTE, VOORBEELDGEMEENTE en VOORBEELDGEMEENTE'
# die de lezer geen informatie geven.
_PLACEHOLDER_LIJST = re.compile(
    r"\bVOORBEELDGEMEENTE"
    r"(?:(?:\s*,\s*|\s+(?:en|of)\s+)VOORBEELDGEMEENTE)+\b"
)


def _collapse_placeholder_lijsten(text: str) -> str:
    return _PLACEHOLDER_LIJST.sub("de betrokken gemeenten", text)


def build_mapping(approved: list[dict]) -> dict[str, str]:
    """Build a {original: replacement} mapping from approved entities."""
    return {e["tekst"]: e["vervanging"] for e in approved}


def apply(text: str, mapping: dict[str, str]) -> str:
    """Apply all replacements to the text.

    Longer matches first to avoid partial replacements.
    Case-insensitive: 'Leidse regio' matches 'Leidse Regio' key.
    Elke key die op woord-karakters begint én eindigt krijgt \\b-wrapping,
    ongeacht lengte. Dat voorkomt dat 'beveiliging' matcht binnen
    'informatiebeveiliging'.
    Post-processing collapst dubbele lidwoorden ('de de' → 'de').
    Lambda replacement avoids re.sub interpreting backslashes.
    """
    for original in sorted(mapping.keys(), key=len, reverse=True):
        replacement = mapping[original]
        patroon = re.escape(original)
        if _heeft_word_grens(original):
            patroon = r"\b" + patroon + r"\b"
        text = re.sub(
            patroon,
            lambda m, r=replacement: r,
            text,
            flags=re.IGNORECASE,
        )
    text = _collapse_placeholder_lijsten(text)
    return _collapse_dubbele_lidwoorden(text)
