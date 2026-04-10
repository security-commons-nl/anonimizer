"""Detect personally identifiable and organisation-specific information via LLM."""
import json
from llm_client import chat


SYSTEM_PROMPT = """Je bent een expert in het detecteren van privacygevoelige en organisatiespecifieke informatie in Nederlandse documenten.

Analyseer de gegeven tekst en identificeer ALLE elementen die vervangen moeten worden voordat het document publiek gedeeld kan worden:

- Persoonsnamen (voor- en achternamen)
- E-mailadressen
- Telefoonnummers
- Organisatienamen (interne namen, afdelingen, programma's)
- Interne projectnamen of codenamen
- Locaties (straatnamen, gebouwnamen)
- Functietitels gekoppeld aan namen
- Interne systeem- of dossiernummers
- Datums die herleidbaar zijn naar personen of specifieke interne events

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
- Gebruik de context: "Bas Stevens" → "de CISO" als hij als CISO wordt beschreven
- Wees consistent: dezelfde entiteit krijgt altijd dezelfde suggestie
- Wees specifiek genoeg: "de afdeling" is beter dan "[verwijderd]"
- E-mailadressen → "[e-mailadres verwijderd]"
- Telefoonnummers → "[telefoonnummer verwijderd]"
"""


def _llm_detect(tekst: str) -> list[dict]:
    """Call LLM and return raw list of detected entities."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyseer deze tekst:\n\n{tekst}"},
    ]
    response = chat(messages, response_format="json")

    try:
        data = json.loads(response)
        entiteiten = data.get("entiteiten", [])
    except json.JSONDecodeError:
        entiteiten = []

    # Deduplicate by tekst
    seen = set()
    unique = []
    for e in entiteiten:
        t = e.get("tekst", "").strip()
        if t and t not in seen:
            seen.add(t)
            unique.append(e)
    return unique


def detect(
    tekst: str,
    memory: list[dict],
    standaard: dict[str, str],
) -> tuple[dict[str, str], list[dict]]:
    """
    Three-layer detection:
      1. Standaard-vervangingen (always-apply config)
      2. Memory (previously confirmed replacements)
      3. LLM NER (for everything not yet known)

    Returns:
        auto_mapping: {original: replacement} — apply silently
        new_entities: [{tekst, categorie, suggestie}] — present to user interactively
    """
    auto_mapping: dict[str, str] = {}

    # Laag 1: standaard-vervangingen
    for original, replacement in standaard.items():
        if original in tekst:
            auto_mapping[original] = replacement

    # Laag 2: memory
    for item in memory:
        t = item.get("tekst", "")
        if t and t in tekst and t not in auto_mapping:
            auto_mapping[t] = item.get("vervanging", "")

    # Laag 3: LLM — only if there is text to analyse
    if not tekst.strip():
        return auto_mapping, []

    llm_entities = _llm_detect(tekst)

    # Filter out what is already covered by auto_mapping
    known = set(auto_mapping.keys())
    new_entities = [e for e in llm_entities if e.get("tekst", "") not in known]

    return auto_mapping, new_entities
