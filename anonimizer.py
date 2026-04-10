#!/usr/bin/env python3
"""
anonimizer — verwijder persoonsgegevens en organisatiespecifieke informatie uit documenten.

Gebruik:
    python anonimizer.py verwerk document.md
    python anonimizer.py verwerk --batch map/
    python anonimizer.py verwerk document.md --output schoon.md
"""
import sys
import os
import pathlib
import click
from detector import detect
from replacer import build_mapping, apply


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
        click.echo("Niets gevonden om te anonimiseren.")
        return []

    click.echo(f"\nGevonden: {len(entiteiten)} element(en) om te beoordelen.\n")
    click.echo("  Enter = suggestie overnemen  |  tekst = eigen vervanging  |  s = overslaan  |  q = stoppen\n")

    approved = []
    for i, e in enumerate(entiteiten, 1):
        tekst = e.get("tekst", "")
        suggestie = e.get("suggestie", "[verwijderd]")
        categorie = CATEGORIE_LABELS.get(e.get("categorie", "overig"), "Overig")

        click.echo(f"[{i}/{len(entiteiten)}] {categorie}: \"{click.style(tekst, fg='yellow')}\"")
        click.echo(f"         Suggestie: \"{click.style(suggestie, fg='green')}\"")

        antwoord = input("         > ").strip()

        if antwoord.lower() == "q":
            click.echo("\nGestopt. Reeds goedgekeurde vervangingen worden toegepast.")
            break
        elif antwoord.lower() == "s":
            click.echo("         Overgeslagen.\n")
            continue
        elif antwoord == "":
            vervanging = suggestie
        else:
            vervanging = antwoord

        approved.append({"tekst": tekst, "vervanging": vervanging})
        click.echo(f"         ✓ \"{tekst}\" → \"{vervanging}\"\n")

    return approved


def verwerk_bestand(pad: pathlib.Path, output_pad: pathlib.Path | None = None) -> None:
    """Process a single file."""
    click.echo(f"\nBestand: {pad}")

    tekst = pad.read_text(encoding="utf-8")

    click.echo("Analyseren met LLM...")
    entiteiten = detect(tekst)

    approved = interactief(entiteiten)

    if not approved:
        click.echo("Geen vervangingen toegepast.")
        return

    mapping = build_mapping(approved)
    resultaat = apply(tekst, mapping)

    if output_pad is None:
        output_pad = pad.parent / f"{pad.stem}-anoniem{pad.suffix}"

    output_pad.write_text(resultaat, encoding="utf-8")
    click.echo(f"\n✓ Opgeslagen als: {output_pad}")
    click.echo(f"  {len(approved)} vervanging(en) toegepast.")


@click.group()
def cli():
    """Anonimizer — verwijder privacygevoelige informatie uit documenten."""
    pass


@cli.command()
@click.argument("pad", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Uitvoerbestand (standaard: <naam>-anoniem.<ext>)")
@click.option("--batch", is_flag=True, help="Verwerk alle .md en .txt bestanden in een map")
def verwerk(pad, output, batch):
    """Verwerk een document of map en verwijder identificerende informatie interactief."""
    if not os.getenv("AI_API_KEY"):
        click.echo("Fout: AI_API_KEY is niet ingesteld. Kopieer .env.example naar .env en vul de sleutel in.", err=True)
        sys.exit(1)

    pad = pathlib.Path(pad)

    if batch or pad.is_dir():
        bestanden = list(pad.glob("*.md")) + list(pad.glob("*.txt"))
        if not bestanden:
            click.echo(f"Geen .md of .txt bestanden gevonden in {pad}.")
            return
        click.echo(f"{len(bestanden)} bestand(en) gevonden.")
        for bestand in bestanden:
            verwerk_bestand(bestand)
    else:
        output_pad = pathlib.Path(output) if output else None
        verwerk_bestand(pad, output_pad)


if __name__ == "__main__":
    cli()
