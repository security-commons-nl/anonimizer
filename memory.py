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
