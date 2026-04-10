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


def detect(text: str) -> list[dict]:
    """Return list of detected entities with suggested replacements."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyseer deze tekst:\n\n{text}"},
    ]
    response = chat(messages, response_format="json")

    try:
        data = json.loads(response)
        entiteiten = data.get("entiteiten", [])
    except json.JSONDecodeError:
        entiteiten = []

    # Deduplicate by tekst, keeping first occurrence
    seen = set()
    unique = []
    for e in entiteiten:
        tekst = e.get("tekst", "").strip()
        if tekst and tekst not in seen:
            seen.add(tekst)
            unique.append(e)

    return unique
