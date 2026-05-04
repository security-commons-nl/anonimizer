"""Self-learning replacement store. Persists confirmed replacements across sessions."""
import json
import pathlib

MEMORY_PAD = pathlib.Path(__file__).parent / "memory.json"


# Generieke lowercase-nouns die als losse memory-key cascade-problemen
# veroorzaken: ze komen als substring voor in samenstellingen
# ('beveiliging' in 'informatiebeveiliging', 'directeur' in 'directeuren').
# Zelfs met \b-wrapping in de replacer blijven deze te generiek om veilig
# globaal te hergebruiken — context bepaalt de juiste vervanging.
BLOCKLIST_GENERIEKE_NOUNS = frozenset({
    "beveiliging",
    "directeur",
    "directie",
    "griffie",
    "griffier",
    "college",
    "receptie",
    "directoraat",
    "afdeling",
    "manager",
    "teamleider",
    "medewerker",
    "leidinggevende",
    "ambtenaar",
})

# Karakters die op mojibake wijzen (kapotte encoding). Entries die deze
# bevatten zijn onbetrouwbaar: ze matchen niet op correct gecodeerde
# documenten en vervuilen het geheugen.
_MOJIBAKE_MARKERS = ("�", "Ã«", "Ã©", "Ã¨", "Ã¯", "Ã¶", "Ã¼")


def valideer_entry(tekst: str, vervanging: str) -> tuple[bool, str]:
    """Bepaal of een memory-entry veilig is om op te slaan.

    Returns (ok, reden). Als ok=False dan is reden een korte uitleg die
    geschikt is om aan de gebruiker te tonen.

    Weigert:
      - lege tekst
      - no-ops (origineel == vervanging, case-insensitive na trim)
      - mojibake in origineel of vervanging
      - losse generieke lowercase-nouns (zie BLOCKLIST_GENERIEKE_NOUNS)
    """
    if not tekst or not tekst.strip():
        return False, "lege tekst"

    if tekst.strip().casefold() == vervanging.strip().casefold():
        return False, "no-op: origineel is identiek aan vervanging"

    samen = tekst + " " + vervanging
    if any(marker in samen for marker in _MOJIBAKE_MARKERS):
        return False, "mojibake: kapotte encoding in tekst of vervanging"

    # Losse generieke noun? (een enkel woord uit de blocklist)
    genormaliseerd = tekst.strip().casefold()
    if " " not in genormaliseerd and genormaliseerd in BLOCKLIST_GENERIEKE_NOUNS:
        return False, (
            f"generiek: {tekst!r} staat op de blocklist — te veel false "
            "positives als los woord"
        )

    return True, ""


def load() -> list[dict]:
    """Return list of {tekst, vervanging, categorie} dicts. Empty list if file does not exist."""
    if not MEMORY_PAD.exists():
        return []
    try:
        data = json.loads(MEMORY_PAD.read_text(encoding="utf-8"))
        return data.get("replacements", [])
    except (json.JSONDecodeError, OSError):
        return []


def save(replacements: list[dict]) -> None:
    """Write the full replacements list to memory.json."""
    MEMORY_PAD.write_text(
        json.dumps({"replacements": replacements}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def lookup(tekst: str, replacements: list[dict]) -> str | None:
    """Return the stored replacement for tekst, or None. Case-sensitive."""
    for item in replacements:
        if item.get("tekst") == tekst:
            return item.get("vervanging")
    return None


def remember(tekst: str, vervanging: str, categorie: str, replacements: list[dict]) -> list[dict]:
    """Add a replacement to the list. No duplicates. Returns updated list.

    Update van een bestaande entry is altijd toegestaan (eerder bevestigd).
    Nieuwe entries worden gevalideerd via valideer_entry — invalide entries
    worden stilletjes overgeslagen. Gebruik valideer_entry in de UI-laag
    om de reden zichtbaar te maken vóór je remember() aanroept.
    """
    # Update-pad: bestaande entry, valideer niet (was al eerder bevestigd).
    for item in replacements:
        if item.get("tekst") == tekst:
            item["vervanging"] = vervanging
            item["categorie"] = categorie
            return replacements

    # Nieuwe entry: valideer voor toevoegen.
    ok, _ = valideer_entry(tekst, vervanging)
    if not ok:
        return replacements

    replacements.append({"tekst": tekst, "vervanging": vervanging, "categorie": categorie})
    return replacements


def detecteer_conflicten(
    replacements: list[dict],
    standaard: dict[str, str],
) -> list[dict]:
    """Vind conflicten binnen en tussen memory en standaard.

    Retourneert een lijst met {type, items, bericht} voor elke gevonden kwestie.
    Wordt bij startup getoond als waarschuwing, blokkeert niet.

    Gedetecteerde conflicttypes:
      - dubbele_key: zelfde tekst in zowel memory als standaard
      - substring: een key is substring van een langere key (risico op
        cascade-vervanging)
      - mojibake: key bevat U+FFFD-karakter (geheugenvervuiling)
    """
    conflicten: list[dict] = []

    mem_keys = {item.get("tekst", ""): item for item in replacements if item.get("tekst")}
    std_keys = set(standaard.keys())

    # Type 1: dubbele key in memory en standaard
    overlap = set(mem_keys.keys()) & std_keys
    for key in overlap:
        mem_val = mem_keys[key].get("vervanging", "")
        std_val = standaard[key]
        if mem_val != std_val:
            conflicten.append({
                "type": "dubbele_key",
                "key": key,
                "memory_vervanging": mem_val,
                "standaard_vervanging": std_val,
                "bericht": f"Key {key!r} staat in zowel memory als standaard met verschillende vervangingen",
            })

    # Type 2: substring-relatie binnen alle keys
    alle_keys = sorted(set(mem_keys.keys()) | std_keys, key=len)
    for i, kort in enumerate(alle_keys):
        if len(kort) < 3:
            continue
        for lang in alle_keys[i + 1:]:
            if kort != lang and kort in lang:
                conflicten.append({
                    "type": "substring",
                    "kort": kort,
                    "lang": lang,
                    "bericht": f"Key {kort!r} is substring van {lang!r} — volgorde van vervanging telt",
                })

    # Type 3: mojibake in memory-key of -vervanging
    for item in replacements:
        tekst = item.get("tekst", "") + " " + item.get("vervanging", "")
        if "�" in tekst or "Ã«" in tekst or "Ã©" in tekst:
            conflicten.append({
                "type": "mojibake",
                "key": item.get("tekst", ""),
                "bericht": f"Mojibake-verdacht karakter in memory-entry {item.get('tekst', '')!r}",
            })

    return conflicten
