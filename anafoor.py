"""Anafoor-linking — Fase E1.

Wanneer een volledige persoonsnaam (voor- + achternaam) is gedetecteerd,
zoekt deze module losse voornaam-verwijzingen verderop in het document en
koppelt ze aan dezelfde vervanging.

Voorbeeld:
    LLM detecteert: {"Bas Stevens": "de CISO"}
    Document bevat later: "Bas meldt dat..."
    → anafoor voegt toe: {"Bas": "de CISO"}

Veiligheidsregels om over-anonimisering te voorkomen:
  1. Voornaam moet ≥ 3 tekens zijn
  2. Voornaam mag geen gangbaar Nederlands woord zijn (zie COMMON_WORDS)
  3. Voornaam moet standalone voorkomen buiten de volle-naam-posities
  4. Geen ambiguïteit: dezelfde voornaam mag niet meerdere unieke
     vervangingen krijgen (bv. twee personen die beiden Jan heten)
"""
import re


# Gangbare Nederlandse woorden die ook als voornaam bestaan maar in gewone
# tekst zelden als zodanig worden bedoeld. Wordt case-insensitive vergeleken.
COMMON_WORDS = {
    "bas",       # ook: muziek-bas, onderste deel
    "mark",      # ook: merk (Engels / product)
    "wil",       # werkwoord
    "daan",      # zeldzaam maar ok
    "tom",       # ook: tom-tom, leeg
    "tim",       # ok
    "kim",       # ambigu
    "max",       # ook: maximum
    "noa",       # kort
    "ava", "amy", "eva",  # korte, ambigu
    "ben", "ron", "rob", "rik",  # ambigu
    "jan", "piet", "klaas",  # zeer gangbaar, ook in "jan-en-alleman"
    "rene", "renee", "rene",
    "cor", "kees",
}

# Minimum lengte van een voornaam om voor anafoor-uitbreiding in aanmerking
# te komen.
MIN_VOORNAAM_LENGTE = 3


def _splits_naam(volle_naam: str) -> tuple[str, str] | None:
    """Splits volle naam in (voornaam, rest). Returnt None bij 1-term namen."""
    delen = volle_naam.strip().split()
    if len(delen) < 2:
        return None
    voornaam = delen[0]
    rest = " ".join(delen[1:])
    return voornaam, rest


def vind_anaforen(
    persoon_mappings: dict[str, str],
    tekst: str,
) -> dict[str, str]:
    """Zoek losse voornaam-verwijzingen voor elke volledige persoonsnaam.

    Args:
        persoon_mappings: {volle_naam: vervanging} — alleen persoon-entries
        tekst: de volledige documenttekst

    Returns:
        {voornaam: vervanging} — extra mappings die veilig toegepast kunnen worden
    """
    # Stap 1: verzamel voornamen en tel unieke vervangingen per voornaam
    voornaam_naar_vervangingen: dict[str, set[str]] = {}

    for volle_naam, vervanging in persoon_mappings.items():
        split = _splits_naam(volle_naam)
        if split is None:
            continue
        voornaam, _ = split
        if len(voornaam) < MIN_VOORNAAM_LENGTE:
            continue
        if voornaam.lower() in COMMON_WORDS:
            continue
        voornaam_naar_vervangingen.setdefault(voornaam, set()).add(vervanging)

    # Stap 2: bepaal welke voornamen eenduidig zijn en daadwerkelijk standalone
    # voorkomen in de tekst (buiten de volle-naam-posities)
    resultaat: dict[str, str] = {}

    for voornaam, vervangingen in voornaam_naar_vervangingen.items():
        if len(vervangingen) != 1:
            # Ambigu: twee personen met dezelfde voornaam, skip
            continue
        vervanging = next(iter(vervangingen))

        # Vind alle posities waar volle namen met deze voornaam voorkomen
        volle_naam_spans: list[tuple[int, int]] = []
        for volle_naam, v in persoon_mappings.items():
            split = _splits_naam(volle_naam)
            if split and split[0] == voornaam:
                for m in re.finditer(re.escape(volle_naam), tekst):
                    volle_naam_spans.append((m.start(), m.end()))

        # Zoek alle standalone voornaam-matches (word-boundary)
        patroon = re.compile(rf"\b{re.escape(voornaam)}\b")
        standalone_gevonden = False
        for m in patroon.finditer(tekst):
            if not any(s <= m.start() < e for s, e in volle_naam_spans):
                standalone_gevonden = True
                break

        if standalone_gevonden:
            resultaat[voornaam] = vervanging

    return resultaat


def expand_persoon_mappings(
    alle_mappings: dict[str, str],
    categorieën: dict[str, str],
    tekst: str,
) -> dict[str, str]:
    """Convenience-functie: verrijk een bestaande mapping met anaforen.

    Args:
        alle_mappings: {origineel: vervanging} — bestaande auto_mapping
        categorieën: {origineel: categorie} — om te bepalen wat 'persoon' is
        tekst: documenttekst

    Returns:
        Nieuwe mapping inclusief anafoor-uitbreidingen (origineel blijft intact).
    """
    persoon_only = {
        k: v for k, v in alle_mappings.items()
        if categorieën.get(k, "").lower() == "persoon"
    }
    anaforen = vind_anaforen(persoon_only, tekst)

    # Voeg alleen toe als de voornaam nog niet als key bestaat
    uitgebreid = dict(alle_mappings)
    for voornaam, vervanging in anaforen.items():
        if voornaam not in uitgebreid:
            uitgebreid[voornaam] = vervanging
    return uitgebreid
