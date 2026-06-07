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
    auto_mapping, entiteiten, bron = detect(tekst, [], {})

    # Deterministische treffers (laag 1/1.5/2, o.a. regex voor BSN/IBAN/e-mail)
    # werken óók zonder LLM-API — die willen we sowieso melden.
    det_regels = [
        f"- **{bron.get(original, 'deterministisch').capitalize()}**: `{original}`"
        for original in auto_mapping
    ]
    llm_regels = [
        f"- **{e.get('categorie', 'overig').capitalize()}**: `{e.get('tekst', '')}`"
        f" (suggestie: _{e.get('suggestie', '')}_)"
        for e in entiteiten
    ]

    if not det_regels and not llm_regels:
        sys.exit(0)

    print(f"### Anonimizer Advies: `{pad.name}`")
    print("")
    print("Ik heb dit bestand gescand en vond de volgende potentieel gevoelige informatie:\n")

    for regel in det_regels + llm_regels:
        print(regel)

    print("")
    print("> Controleer of deze termen bewust gebruikt worden of dat de lokale")
    print("> [anonimizer](https://github.com/security-commons-nl/anonimizer) over dit document gedraaid moet worden.")
    print("")


if __name__ == "__main__":
    main()
