"""Self-learning replacement store. Persists confirmed replacements across sessions."""
import json
import pathlib

MEMORY_PAD = pathlib.Path(__file__).parent / "memory.json"


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
    """Add a replacement to the list (no duplicates). Returns updated list."""
    for item in replacements:
        if item.get("tekst") == tekst:
            item["vervanging"] = vervanging
            item["categorie"] = categorie
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
