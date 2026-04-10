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

    # Determine output paths
    if output_pad is None:
        md_pad = pad.parent / f"{pad.stem}-anoniem.md"
    else:
        md_pad = output_pad if output_pad.suffix == ".md" else output_pad.with_suffix(".md")

    html_pad = md_pad.with_suffix(".html")

    # Write .md
    md_pad.write_text(resultaat, encoding="utf-8")

    # Write .html
    html_body = md_lib.markdown(resultaat, extensions=["tables"])
    html_inhoud = (
        "<!DOCTYPE html>\n"
        "<html lang=\"nl\">\n"
        "<meta charset=\"utf-8\">\n"
        "<body>\n"
        f"{html_body}\n"
        "</body>\n"
        "</html>"
    )
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
