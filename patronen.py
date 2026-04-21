"""Deterministic regex-based detection for structured identifiers.

Layer 1.5 — runs between standaard.yaml and memory. LLMs are unreliable for these
structured patterns; regex gives 100% recall for what it covers, with no false
positives when the patterns are anchored correctly.

Each pattern returns a normalised placeholder so results are consistent.
"""
import re
from typing import Iterable


# --- Patronen ---------------------------------------------------------------

# E-mail: RFC-5322 light, genoeg voor documenttekst.
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# NL-telefoon: accepteert +31 of 0 prefix, gevolgd door 8-10 cijfers met
# optionele spaties of koppeltekens ertussen. Voldoende permissief voor
# varianten als "070 373 80 11", "06-12345678", "+31 (0)20 1234567".
# Negative lookbehind/ahead op \w voorkomt matches binnen langere cijferreeksen
# (IBAN, BSN) en in versie/datum-notaties zoals "v1.0 0.5".
_TELEFOON = re.compile(
    r"(?<!\w)"
    r"(?:\+31[\s\-]?\(?0?\)?|0)"      # landcode of nationaal prefix
    r"(?:[\s\-]?\d){8,10}"             # 8-10 resterende cijfers
    r"(?!\w)"
)

# NL-postcode: 1234 AB (optionele spatie). Hoofdletters verplicht.
_POSTCODE = re.compile(r"\b[1-9]\d{3}\s?[A-Z]{2}\b")

# IPv4: geldige octetten, met extra eis dat minstens één octet ≥100
# om typische hoofdstuk/versienummers ("14.2.7.1", "1.2.3.4") uit te filteren.
_IPV4_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_IPV4 = re.compile(
    rf"(?<!\d\.)\b(?={_IPV4_OCTET}\.{_IPV4_OCTET}\.{_IPV4_OCTET}\.{_IPV4_OCTET}\b)"
    rf"(?=(?:\d+\.){{0,3}}[12]\d{{2}})"   # minstens één octet begint met 1 of 2 (≥100)
    rf"{_IPV4_OCTET}\.{_IPV4_OCTET}\.{_IPV4_OCTET}\.{_IPV4_OCTET}\b"
)

# KVK: 8-cijferig, vaak voorafgegaan door "KVK" of "kvk-nummer".
# Accepteert "KVK 12345678" en "KVK: 12345678".
_KVK = re.compile(r"\bKVK[\s:]*(\d{8})\b", re.IGNORECASE)

# FG-nummer (AP-register): FG gevolgd door 6 cijfers.
_FG_NUMMER = re.compile(r"\bFG[\s:]*(\d{6})\b")

# IBAN NL: NL + 2 cijfers + 4 letters + 10 cijfers (met optionele spaties per 4).
_IBAN_NL = re.compile(
    r"\bNL\d{2}\s?[A-Z]{4}\s?\d{4}\s?\d{4}\s?\d{2}\b"
)

# BSN: 9 cijfers. Validatie met 11-proef om false positives te voorkomen
# (bv. pagina-nummers, telefoonnummers, versie-codes).
_BSN_KANDIDAAT = re.compile(r"(?<!\d)(\d{9})(?!\d)")


def _is_geldig_bsn(nummer: str) -> bool:
    """11-proef voor BSN: som van cijfer*gewicht moet deelbaar door 11 zijn.
    Gewichten zijn 9,8,7,6,5,4,3,2,-1.
    """
    if len(nummer) != 9 or not nummer.isdigit():
        return False
    if nummer == "000000000":
        return False
    gewichten = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    totaal = sum(int(c) * g for c, g in zip(nummer, gewichten))
    return totaal % 11 == 0


# --- Detectie ---------------------------------------------------------------

PATROON_DETECTORS = [
    # (naam, regex, categorie, vervanging, optionele validator)
    ("email",    _EMAIL,    "email",    "[e-mailadres verwijderd]", None),
    ("telefoon", _TELEFOON, "telefoon", "[telefoonnummer verwijderd]", None),
    ("iban",     _IBAN_NL,  "nummer",   "[IBAN verwijderd]", None),
    ("kvk",      _KVK,      "nummer",   "[KVK-nummer verwijderd]", None),
    ("fg",       _FG_NUMMER,"nummer",   "[FG-nummer verwijderd]", None),
    ("postcode", _POSTCODE, "locatie",  "[postcode verwijderd]", None),
    ("ipv4",     _IPV4,     "nummer",   "[IP-adres verwijderd]", None),
    ("bsn",     _BSN_KANDIDAAT, "nummer", "[BSN verwijderd]", _is_geldig_bsn),
]


def detect_patronen(tekst: str) -> tuple[dict[str, str], list[dict]]:
    """Vind alle deterministische patronen in tekst.

    Retourneert:
        mapping: {originele_tekst: vervanging} — kan direct op tekst toegepast worden
        entiteiten: [{tekst, categorie, suggestie, bron}] — voor audit/rapport
    """
    mapping: dict[str, str] = {}
    entiteiten: list[dict] = []

    for naam, patroon, categorie, vervanging, validator in PATROON_DETECTORS:
        for match in patroon.finditer(tekst):
            origineel = match.group(0)

            if validator is not None and not validator(match.group(1) if match.groups() else origineel):
                continue

            if origineel in mapping:
                continue

            mapping[origineel] = vervanging
            entiteiten.append({
                "tekst": origineel,
                "categorie": categorie,
                "suggestie": vervanging,
                "bron": f"patroon:{naam}",
            })

    return mapping, entiteiten


def filter_bekend(entiteiten: Iterable[dict], bekende_teksten: set[str]) -> list[dict]:
    """Filter entiteiten waarvan de tekst al in auto_mapping zit."""
    return [e for e in entiteiten if e.get("tekst", "") not in bekende_teksten]
