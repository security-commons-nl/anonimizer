#!/usr/bin/env python3
"""
ci_scanner.py — Non-interactive wrapper for anonimizer detector.
Used in GitHub Actions to post advisory comments on Pull Requests.

Gebruik:
    python ci_scanner.py <pad_naar_bestand>

Uitvoer: markdown-tekst op stdout (leeg als er niets gevonden is).
Sluit af met code 0, ook als er bevindingen zijn (niet blokkerend).
"""
import sys
import pathlib
from converter import to_markdown
from detector import detect


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python ci_scanner.py <pad_naar_bestand>")
        sys.exit(1)

    pad = pathlib.Path(sys.argv[1])
    if not pad.exists():
        print(f"Bestaat niet: {pad}", file=sys.stderr)
        sys.exit(1)

    try:
        tekst = to_markdown(pad)
    except ValueError:
        # Unsupported format — skip silently in CI
        sys.exit(0)

    if not tekst.strip():
        sys.exit(0)

    # In CI: no memory, no standaard config (by design — more noise is acceptable)
    _, entiteiten = detect(tekst, [], {})

    if not entiteiten:
        sys.exit(0)

    print(f"### Anonimizer Advies: `{pad.name}`")
    print("")
    print("Ik heb dit bestand gescand en vond de volgende potentieel gevoelige informatie:\n")

    for e in entiteiten:
        t = e.get("tekst", "")
        c = e.get("categorie", "overig").capitalize()
        s = e.get("suggestie", "")
        print(f"- **{c}**: `{t}` (suggestie: _{s}_)")

    print("")
    print("> Controleer of deze termen bewust gebruikt worden of dat de lokale")
    print("> [anonimizer](https://github.com/security-commons-nl/anonimizer) over dit document gedraaid moet worden.")
    print("")


if __name__ == "__main__":
    main()
