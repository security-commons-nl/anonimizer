#!/usr/bin/env python3
"""
anonimizer — verwijder persoonsgegevens en organisatiespecifieke informatie uit documenten.

Gebruik:
    python anonimizer.py verwerk document.pdf
    python anonimizer.py verwerk document.docx
    python anonimizer.py verwerk map/ --batch
    python anonimizer.py verwerk document.md --output schoon.md
"""
import sys
import os
import json
import pathlib
import click

# Force UTF-8 on stdout/stderr so Windows cp1252 consoles don't crash on
# box-drawing characters (─, →) used in our output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import markdown as md_lib
from converter import to_markdown, ONDERSTEUNDE_EXTENSIES
from detector import detect, voeg_anaforen_toe
from replacer import build_mapping, apply
from audit import AuditLog
import memory
import standaard


CATEGORIE_LABELS = {
    "persoon": "Persoon",
    "email": "E-mailadres",
    "telefoon": "Telefoonnummer",
    "organisatie": "Organisatie",
    "project": "Project/programma",
    "locatie": "Locatie",
    "functie": "Functie",
    "nummer": "Intern nummer",
    "datum": "Datum",
    "overig": "Overig",
}


def interactief(entiteiten: list[dict]) -> list[dict]:
    """Loop through detected entities and let user confirm/adjust/skip each."""
    if not entiteiten:
        return []

    if not sys.stdin.isatty():
        click.echo(
            f"\n  Gevonden: {len(entiteiten)} nieuw element(en) — overgeslagen "
            "(geen interactieve terminal). Alleen auto-vervangingen toegepast.\n"
        )
        return []

    click.echo(f"\n  Gevonden: {len(entiteiten)} nieuw element(en).\n")
    click.echo("  Enter = suggestie overnemen  |  tekst = eigen vervanging  |  s = overslaan  |  q = stoppen\n")

    approved = []
    for i, e in enumerate(entiteiten, 1):
        tekst = e.get("tekst", "")
        suggestie = e.get("suggestie", "[verwijderd]")
        categorie = CATEGORIE_LABELS.get(e.get("categorie", "overig"), "Overig")

        click.echo(f"  [{i}/{len(entiteiten)}] {categorie}: \"{click.style(tekst, fg='yellow')}\"")
        click.echo(f"           Suggestie: \"{click.style(suggestie, fg='green')}\"")

        antwoord = input("           > ").strip()

        if antwoord.lower() == "q":
            click.echo("\n  Gestopt. Reeds goedgekeurde vervangingen worden toegepast.")
            break
        elif antwoord.lower() == "s":
            click.echo("           Overgeslagen.\n")
            continue
        elif antwoord == "":
            vervanging = suggestie
        else:
            vervanging = antwoord

        approved.append({"tekst": tekst, "vervanging": vervanging, "categorie": e.get("categorie", "overig")})
        click.echo(f"           \"{tekst}\" -> \"{vervanging}\"\n")

    return approved


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titel}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
      font-size: 1rem;
      line-height: 1.75;
      color: #1a1a1a;
      background: #f3f4f6;
      margin: 0;
      padding: 2rem 1rem;
    }}
    .document {{
      max-width: 800px;
      margin: 0 auto;
      background: #fff;
      padding: 3rem 4rem;
      box-shadow: 0 1px 4px rgba(0,0,0,.12);
    }}
    .anonimizer-banner {{
      font-size: .78rem;
      color: #6b7280;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: .375rem;
      padding: .4rem .75rem;
      margin-bottom: 2.5rem;
    }}
    .anonimizer-banner a {{ color: #4b5563; }}
    h1 {{ font-size: 1.75rem; line-height: 1.3; margin: 2rem 0 1rem; color: #111; }}
    h2 {{ font-size: 1.35rem; line-height: 1.3; margin: 2rem 0 .75rem; color: #1a1a1a;
          border-bottom: 2px solid #e5e7eb; padding-bottom: .35rem; }}
    h3 {{ font-size: 1.1rem; margin: 1.5rem 0 .5rem; color: #1a1a1a; }}
    h4 {{ font-size: 1rem; margin: 1.25rem 0 .4rem; font-weight: 600; }}
    p {{ margin: 0 0 1rem; }}
    ul, ol {{ margin: 0 0 1rem; padding-left: 1.5rem; }}
    li {{ margin-bottom: .25rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 1.5rem; font-size: .92rem; }}
    th {{ background: #f3f4f6; font-weight: 600; text-align: left; }}
    th, td {{ border: 1px solid #d1d5db; padding: .5rem .75rem; vertical-align: top; }}
    tr:nth-child(even) td {{ background: #f9fafb; }}
    hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }}
    mark.placeholder {{
      background: #fef9c3;
      color: #713f12;
      border-radius: .2rem;
      padding: .05em .3em;
      font-size: .88em;
      font-family: ui-monospace, monospace;
      font-style: normal;
    }}
    mark.placeholder-afbeelding {{
      background: #fee2e2;
      color: #7f1d1d;
      border-radius: .2rem;
      padding: .2em .5em;
      font-size: .88em;
      font-family: ui-monospace, monospace;
      display: inline-block;
      margin: .5rem 0;
    }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .document {{ box-shadow: none; padding: 0; }}
      .anonimizer-banner {{ display: none; }}
      mark.placeholder {{ border: 1px solid #d97706; background: #fef9c3; }}
    }}
    @media (max-width: 640px) {{
      .document {{ padding: 1.5rem; }}
    }}
  </style>
</head>
<body>
<div class="document">
  <div class="anonimizer-banner">
    Geanonimiseerd met <a href="https://github.com/security-commons-nl/anonimizer"
    target="_blank" rel="noopener">anonimizer</a> &mdash; security-commons-nl.
    Gele markering = vervangen tekst.
  </div>
  {body}
</div>
</body>
</html>
"""


def _naar_html(tekst: str, bestandsnaam: str) -> str:
    """Convert anonymised markdown to a styled standalone HTML document."""
    import re as _re
    html_body = md_lib.markdown(tekst, extensions=["tables"])

    # Highlight [AFBEELDING VERWIJDERD]
    html_body = _re.sub(
        r'\[AFBEELDING VERWIJDERD\]',
        '<mark class="placeholder-afbeelding">[AFBEELDING VERWIJDERD]</mark>',
        html_body,
    )
    # Highlight all other [xxx verwijderd] placeholders
    html_body = _re.sub(
        r'\[([^\]]+(?:verwijderd|verwijderde)[^\]]*)\]',
        r'<mark class="placeholder">[\1]</mark>',
        html_body,
        flags=_re.IGNORECASE,
    )

    return _HTML_TEMPLATE.format(
        titel=bestandsnaam,
        body=html_body,
    )


def verwerk_bestand(
    pad: pathlib.Path,
    output_pad: pathlib.Path | None = None,
    dry_run: bool = False,
    audit_log: AuditLog | None = None,
) -> None:
    """Process a single file: convert, detect, replace, write .md + .html.

    In dry_run modus: alleen detectie, geen wegschrijven, JSON-rapport op stdout.
    Als audit_log gegeven is: elke vervanging wordt gelogd met bron-laag.
    """
    click.echo(f"\n{'─' * 60}")
    click.echo(f"  Bestand: {click.style(str(pad), bold=True)}")

    # Load memory and standaard-vervangingen
    mem = memory.load()
    std = standaard.laad()

    # Convert to markdown
    try:
        tekst = to_markdown(pad)
    except ValueError as e:
        click.echo(f"  Overgeslagen: {e}", err=True)
        return

    if not tekst.strip():
        click.echo("  Leeg bestand, overgeslagen.")
        return

    click.echo(f"  Analyseren... ({len(tekst)} tekens)")

    # Detect (3 layers)
    auto_mapping, new_entities, bron = detect(tekst, mem, std)

    # Anafoor: voeg losse voornamen toe die verwijzen naar reeds gedetecteerde personen.
    # Metadata = memory + LLM-resultaten (LLM bevat categorie; memory ook).
    metadata_voor_anafoor = list(mem) + new_entities
    _, anafoor_mapping = voeg_anaforen_toe(
        {**auto_mapping, **{e["tekst"]: e.get("suggestie", "") for e in new_entities}},
        metadata_voor_anafoor,
        tekst,
    )

    # --- dry-run: rapporteer en stop ---
    if dry_run:
        rapport = {
            "bestand": str(pad),
            "tekens": len(tekst),
            "auto_mapping": [
                {"tekst": orig, "vervanging": repl, "bron": bron.get(orig, "?")}
                for orig, repl in sorted(auto_mapping.items())
            ],
            "llm_entiteiten": new_entities,
            "anaforen": [
                {"tekst": k, "vervanging": v, "bron": "anafoor"}
                for k, v in sorted(anafoor_mapping.items())
            ],
            "totaal": len(auto_mapping) + len(new_entities) + len(anafoor_mapping),
        }
        click.echo(json.dumps(rapport, ensure_ascii=False, indent=2))
        return

    # Show auto-applied
    if auto_mapping:
        click.echo(f"  Automatisch toegepast: {len(auto_mapping)} vervanging(en) (standaard + geheugen + patroon)")
        for orig, repl in sorted(auto_mapping.items()):
            click.echo(f"    - \"{orig}\" -> \"{repl}\" [{bron.get(orig, '?')}]")
            if audit_log:
                audit_log.log(str(pad), orig, repl, bron.get(orig, "?"))

    # Interactive loop for new entities
    approved = interactief(new_entities)

    # Save newly confirmed to memory
    if approved:
        for item in approved:
            mem = memory.remember(item["tekst"], item["vervanging"], item.get("categorie", "overig"), mem)
            if audit_log:
                audit_log.log(
                    str(pad), item["tekst"], item["vervanging"],
                    "llm+bevestigd", item.get("categorie", ""),
                )
        memory.save(mem)

    if not auto_mapping and not approved:
        click.echo("  Geen vervangingen toegepast.")
        return

    # Build full mapping
    full_mapping = {**auto_mapping, **build_mapping(approved)}

    # Anafoor: breid uit met losse voornamen van bevestigde personen (Fase E1)
    metadata_voor_anafoor = list(mem) + approved
    full_mapping, anafoor_mapping = voeg_anaforen_toe(
        full_mapping, metadata_voor_anafoor, tekst
    )
    if anafoor_mapping:
        click.echo(f"  Anafoor-uitbreidingen: {len(anafoor_mapping)}")
        for orig, repl in sorted(anafoor_mapping.items()):
            click.echo(f"    - \"{orig}\" -> \"{repl}\" [anafoor]")
            if audit_log:
                audit_log.log(str(pad), orig, repl, "anafoor")

    resultaat = apply(tekst, full_mapping)

    # Second pass: re-apply standaard to catch strings introduced by memory replacements
    if std:
        resultaat = apply(resultaat, std)

    # Determine output paths
    if output_pad is None:
        md_pad = pad.parent / f"{pad.stem}-anoniem.md"
    else:
        md_pad = output_pad if output_pad.suffix == ".md" else output_pad.with_suffix(".md")

    html_pad = md_pad.with_suffix(".html")

    # Write .md
    md_pad.write_text(resultaat, encoding="utf-8")

    # Write .html
    html_inhoud = _naar_html(resultaat, pad.stem)
    html_pad.write_text(html_inhoud, encoding="utf-8")

    click.echo(f"\n  Opgeslagen:")
    click.echo(f"    {click.style(str(md_pad), fg='green')} (.md)")
    click.echo(f"    {click.style(str(html_pad), fg='green')} (.html)")
    click.echo(f"    {len(auto_mapping)} automatisch, {len(approved)} bevestigd.")


@click.group()
def cli():
    """Anonimizer — verwijder privacygevoelige informatie uit documenten."""
    pass


@cli.command()
@click.argument("pad", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Uitvoerbestand (standaard: <naam>-anoniem.md + .html)")
@click.option("--batch", is_flag=True,
              help="Verwerk alle ondersteunde bestanden in een map")
@click.option("--dry-run", is_flag=True,
              help="Toon alleen detecties als JSON, schrijf geen output")
@click.option("--audit", type=click.Path(), default=None,
              help="Schrijf per vervanging een JSONL-auditregel naar dit bestand")
def verwerk(pad, output, batch, dry_run, audit):
    """Verwerk een document of map en verwijder identificerende informatie interactief.

    Ondersteunde formaten: .md, .txt, .html, .htm, .docx, .pdf, .pptx, .xlsx
    Uitvoer is altijd zowel .md als .html.
    """
    if not os.getenv("AI_API_KEY"):
        click.echo(
            "Fout: AI_API_KEY is niet ingesteld. "
            "Kopieer .env.example naar .env en vul de sleutel in.",
            err=True,
        )
        sys.exit(1)

    pad = pathlib.Path(pad)
    audit_log = AuditLog(audit) if audit else None

    # Conflict-detectie: waarschuw bij dubbele keys, substring-overlap, mojibake
    conflicten = memory.detecteer_conflicten(memory.load(), standaard.laad())
    if conflicten:
        click.echo(click.style(
            f"⚠ {len(conflicten)} conflict(en) in memory/standaard — "
            "detectie werkt maar resultaat kan inconsistent zijn:",
            fg="yellow"
        ), err=True)
        for c in conflicten[:10]:  # max 10 tonen
            click.echo(f"    [{c['type']}] {c['bericht']}", err=True)
        if len(conflicten) > 10:
            click.echo(f"    ... en nog {len(conflicten) - 10} meer", err=True)
        click.echo("", err=True)

    try:
        if batch or pad.is_dir():
            bestanden = []
            for ext in ONDERSTEUNDE_EXTENSIES:
                bestanden.extend(pad.glob(f"*{ext}"))
            bestanden = sorted(set(bestanden))

            if not bestanden:
                click.echo(f"Geen ondersteunde bestanden gevonden in {pad}.")
                click.echo(f"Ondersteund: {', '.join(sorted(ONDERSTEUNDE_EXTENSIES))}")
                return

            click.echo(f"{len(bestanden)} bestand(en) gevonden.")
            for bestand in bestanden:
                verwerk_bestand(bestand, dry_run=dry_run, audit_log=audit_log)

            click.echo(f"\n{'=' * 60}")
            click.echo("Klaar.")
        else:
            output_pad = pathlib.Path(output) if output else None
            verwerk_bestand(pad, output_pad, dry_run=dry_run, audit_log=audit_log)
    finally:
        if audit_log:
            audit_log.sluit()
            click.echo(f"\nAudit-log: {audit}")


if __name__ == "__main__":
    # Load .env if present
    env_pad = pathlib.Path(__file__).parent / ".env"
    if env_pad.exists():
        for line in env_pad.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    cli()
