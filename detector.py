"""Detect personally identifiable and organisation-specific information.

Drie-laagse detectie:
  1.   standaard.yaml — org-specifieke always-apply vervangingen
  1.5  patronen.py   — deterministische regex voor gestructureerde IDs
  2.   memory.json   — eerder bevestigde vervangingen
  3.   LLM NER       — namen/organisaties/context (Mistral of equivalent)
  3.5  allowlist     — post-filter voor LLM: afkortingen/publieke organisaties
                       die de LLM soms ten onrechte markeert
"""
import json
from llm_client import chat
from patronen import detect_patronen
from anafoor import expand_persoon_mappings


# Allowlist: exacte strings die nooit vervangen mogen worden, ongeacht wat
# de LLM zegt. Afkortingen uit officiële tabellen (AVG, BSN, etc.) en
# publieke organisaties. Case-insensitive vergelijking.
ALLOWLIST = {
    # Rollen/functies als afkorting (niet persoon-specifiek)
    "ciso", "iso", "cio", "fg", "raci",
    # Wetten en standaarden
    "avg", "wpg", "wgbo", "bio", "big", "bsn", "ict", "it", "iban",
    "nta", "nen", "kvk", "wvggz", "ap", "saas", "mdr",
    # Publieke organisaties en diensten
    "ibd", "vng", "ncsc", "ap", "autoriteit persoonsgegevens",
    "informatiebeveiligingsdienst", "informatiebeveiligingsdienst voor gemeenten",
    "vereniging van nederlandse gemeenten", "rijksoverheid",
    "nationaal cyber security centrum", "agentschap telecom",
    "baseline informatiebeveiliging overheid", "basisregistratie personen",
    # Generieke begrippen / rolcategorieën
    "chief information security officer", "information security officer",
    "functionaris gegevensbescherming",
    "algemene verordening gegevensbescherming",
    "wet op de geneeskundige behandelingsovereenkomst",
    "privacy officer", "data protection officer",
    # Interne calamiteitenteams (algemene termen)
    "ctd", "calamiteitenteam digitaal", "calamiteiten team digitaal",
    # Generieke software/diensten (niet-specifiek)
    "microsoft teams", "outlook", "topdesk", "join", "sharepoint",
    "root cause analysis", "reason for outage", "mermaid",
}


def _in_allowlist(tekst: str) -> bool:
    """Check of een gedetecteerde string op de allowlist staat."""
    return tekst.strip().lower() in ALLOWLIST


SYSTEM_PROMPT = """Je bent een expert in het detecteren van privacygevoelige en organisatiespecifieke informatie in Nederlandse documenten van gemeenten en publieke organisaties.

Analyseer de gegeven tekst en identificeer ALLE elementen die vervangen moeten worden voordat het document publiek gedeeld kan worden:

**WEL detecteren:**
- Persoonsnamen — óók losse voornamen (Khalid, Frank), niet-Nederlandse achternamen (Errami, IJzerman), namen met tussenvoegsels (van der Meer, de Vries, 't Hart)
- E-mailadressen, telefoonnummers, postcodes, IP-adressen
- Interne organisatie- en afdelingsnamen, projectcodes
- Externe leveranciers genoemd als klant-partner (bv. "onze MDR-leverancier Arctic Wolf")
- Functietitels gekoppeld aan specifieke personen
- Interne dossier-, zaak- of systeemnummers
- Datums die herleidbaar zijn naar personen of unieke interne events
- Interne URLs en portalen (bv. virtueel.servicepunt71.nl)

**NIET detecteren (moeten in het document blijven staan):**
- Formulier- of kolomkoppen zonder concrete waarde: "Naam", "Telefoonnummer", "E-mailadres", "Organisatie", "Geslacht", "Geboortedatum", "Adres" — dit zijn labels in een formulier, geen data
- Afkortingen uit officiële tabellen: AVG, AP, FG, CISO, ISO, CIO, BIO, BIG, BSN, AVG, Wpg, ICT, RACI, NTA, NEN
- Functietitels in rol-beschrijvingen zónder persoonsnaam ("De CISO is verantwoordelijk voor...")
- Publieke organisaties/standaarden die algemeen bekend zijn:
  IBD (Informatiebeveiligingsdienst), VNG, NCSC, Autoriteit Persoonsgegevens, AP,
  Baseline Informatiebeveiliging Overheid (BIO), BIG, Basisregistratie Personen,
  Rijksoverheid, Nationaal Cyber Security Centrum
- Generieke software-/methode-namen: Microsoft Teams, Topdesk, JOIN, Sharepoint, Outlook, Root Cause Analysis, Mermaid

Geef je antwoord als JSON met deze structuur:
{
  "entiteiten": [
    {
      "tekst": "de exacte tekst zoals die in het document staat",
      "categorie": "persoon|email|telefoon|organisatie|project|locatie|functie|nummer|datum|overig",
      "suggestie": "een neutrale vervangende tekst"
    }
  ]
}

Regels voor suggesties:
- Gebruik de context: "Bas Stevens (CISO)" → suggestie "de CISO"
- Wees consistent: dezelfde entiteit krijgt dezelfde suggestie, ook bij losse voornaam ("Bas" later in doc ook → "de CISO")
- Wees specifiek genoeg: "de afdeling" of "de leverancier" is beter dan "[verwijderd]"
- E-mailadressen → "[e-mailadres verwijderd]"
- Telefoonnummers → "[telefoonnummer verwijderd]"
- Als twijfel tussen persoonsnaam of gewoon woord: als het met hoofdletter staat en grammaticaal als naam functioneert → persoon

Voorbeelden:
- "Opgesteld door Khalid en Frank" → beide zijn persoon (losse voornamen)
- "informeer de Privacy Officers Bart Kock en Dimitri IJzerman" → Bart Kock en Dimitri IJzerman zijn personen
- "Bijlage 3: Topdesk formulier Aanmelder Naam Telefoonnummer E-mail Organisatie" → NIET detecteren (formulierlabels)
- "De IBD is het CERT voor gemeenten" → IBD niet vervangen (publieke organisatie)
- "goedgekeurd door Bas Stevens (CISO)" → "Bas Stevens" vervangen door "de CISO"
"""


# Maximaal aantal tekens per LLM-chunk. Documenten boven deze lengte worden
# opgesplitst op paragraaf-grenzen om te voorkomen dat de LLM (of het
# context-window) items over het hoofd ziet in lange documenten.
_CHUNK_GROOTTE = 8000
_CHUNK_OVERLAP = 400


def _chunk_tekst(tekst: str, grootte: int = _CHUNK_GROOTTE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Splits tekst in chunks op paragraaf-grenzen, met overlap om te voorkomen
    dat entiteiten precies op een grens worden doorgesneden."""
    if len(tekst) <= grootte:
        return [tekst]

    chunks = []
    start = 0
    n = len(tekst)
    while start < n:
        eind = min(start + grootte, n)
        if eind < n:
            # Zoek dichtstbijzijnde paragraaf-einde vóór eind
            laatste_para = tekst.rfind("\n\n", start + grootte // 2, eind)
            if laatste_para != -1:
                eind = laatste_para
        chunks.append(tekst[start:eind])
        if eind >= n:
            break
        start = max(eind - overlap, start + 1)
    return chunks


def _llm_detect_chunk(tekst: str) -> list[dict]:
    """Call LLM op één chunk en retourneer ruwe lijst."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyseer deze tekst:\n\n{tekst}"},
    ]
    response = chat(messages, response_format="json")
    try:
        return json.loads(response).get("entiteiten", [])
    except json.JSONDecodeError:
        return []


def _llm_detect(tekst: str) -> list[dict]:
    """Call LLM en retourneer gededupliceerde, gefilterde lijst.

    Voor lange documenten: splits in chunks, verzamel resultaten, dedupliceer.
    Allowlist-filter voorkomt dat afkortingen/publieke organisaties worden
    vervangen ook als de LLM ze ten onrechte markeert.
    """
    chunks = _chunk_tekst(tekst)
    alle_entiteiten: list[dict] = []
    for chunk in chunks:
        alle_entiteiten.extend(_llm_detect_chunk(chunk))

    seen = set()
    unique = []
    for e in alle_entiteiten:
        t = e.get("tekst", "").strip()
        if not t or t in seen:
            continue
        if _in_allowlist(t):
            continue
        seen.add(t)
        unique.append(e)
    return unique


def detect(
    tekst: str,
    memory: list[dict],
    standaard: dict[str, str],
) -> tuple[dict[str, str], list[dict], dict[str, str]]:
    """Drie-laagse detectie (zie module-docstring).

    Returns:
        auto_mapping: {original: replacement} — apply silently (laag 1, 1.5, 2)
        new_entities: [{tekst, categorie, suggestie, bron}] — present interactively (laag 3)
        bron: {original: laagnaam} — voor audit-trail
    """
    auto_mapping: dict[str, str] = {}
    bron: dict[str, str] = {}

    # Laag 1: standaard-vervangingen
    for original, replacement in standaard.items():
        if original in tekst:
            auto_mapping[original] = replacement
            bron[original] = "standaard"

    # Laag 1.5: deterministische regex-patronen
    patroon_mapping, _ = detect_patronen(tekst)
    for original, replacement in patroon_mapping.items():
        if original not in auto_mapping:
            auto_mapping[original] = replacement
            bron[original] = "patroon"

    # Laag 2: memory
    for item in memory:
        t = item.get("tekst", "")
        if t and t in tekst and t not in auto_mapping:
            auto_mapping[t] = item.get("vervanging", "")
            bron[t] = "geheugen"

    # Laag 3: LLM — alleen als er tekst is
    if not tekst.strip():
        return auto_mapping, [], bron

    llm_entities = _llm_detect(tekst)

    # Filter wat al gedekt is door eerdere lagen
    known = set(auto_mapping.keys())
    new_entities = [
        {**e, "bron": "llm"}
        for e in llm_entities
        if e.get("tekst", "") not in known
    ]

    return auto_mapping, new_entities, bron


def voeg_anaforen_toe(
    mapping: dict[str, str],
    entiteiten_metadata: list[dict],
    tekst: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Verrijk een mapping met losse voornaam-verwijzingen (Fase E1).

    Args:
        mapping: {origineel: vervanging} — huidige actieve mapping
        entiteiten_metadata: lijst van {tekst, categorie, ...} waarmee we
            weten welke keys 'persoon' zijn. Komt uit memory + approved/LLM.
        tekst: documenttekst

    Returns:
        (uitgebreide_mapping, anafoor_mapping)
        uitgebreide_mapping bevat alles uit mapping + gevonden anaforen
        anafoor_mapping bevat alleen de nieuw toegevoegde voornaam→vervanging
    """
    categorieën = {
        e.get("tekst", ""): e.get("categorie", "")
        for e in entiteiten_metadata
        if e.get("tekst")
    }
    uitgebreid = expand_persoon_mappings(mapping, categorieën, tekst)
    anafoor_mapping = {k: v for k, v in uitgebreid.items() if k not in mapping}
    return uitgebreid, anafoor_mapping
