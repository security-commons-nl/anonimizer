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
import pathlib
import click

# Force UTF-8 on stdout/stderr so Windows cp1252 consoles don't crash on
# box-drawing characters (─, →) used in our output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import markdown as md_lib
from converter import to_markdown, ONDERSTEUNDE_EXTENSIES
from detector import detect
from replacer import build_mapping, apply
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


def verwerk_bestand(pad: pathlib.Path, output_pad: pathlib.Path | None = None) -> None:
    """Process a single file: convert, detect, replace, write .md + .html."""
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
    auto_mapping, new_entities = detect(tekst, mem, std)

    # Show auto-applied
    if auto_mapping:
        click.echo(f"  Automatisch toegepast: {len(auto_mapping)} vervanging(en) (standaard + geheugen)")
        for orig, repl in sorted(auto_mapping.items()):
            click.echo(f"    - \"{orig}\" -> \"{repl}\"")

    # Interactive loop for new entities
    approved = interactief(new_entities)

    # Save newly confirmed to memory
    if approved:
        for item in approved:
            mem = memory.remember(item["tekst"], item["vervanging"], item.get("categorie", "overig"), mem)
        memory.save(mem)

    if not auto_mapping and not approved:
        click.echo("  Geen vervangingen toegepast.")
        return

    # Build full mapping and apply
    full_mapping = {**auto_mapping, **build_mapping(approved)}
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
def verwerk(pad, output, batch):
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
            verwerk_bestand(bestand)

        click.echo(f"\n{'=' * 60}")
        click.echo("Klaar.")
    else:
        output_pad = pathlib.Path(output) if output else None
        verwerk_bestand(pad, output_pad)


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
