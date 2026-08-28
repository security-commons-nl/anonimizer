"""Gedeelde PII-fixture: elk geval uit tests/fixtures/pii-patronen.json door patronen.py.

Dit bestand is de CANONIEKE fixture. anonimizer-browser en publicatiescan dragen een
byte-identieke kopie plus een sha256 (zie hun README). Wijzig je hier iets, werk dan
de kopieen en hashes daar bij.

Draaien: pytest tests/test_fixture_gedeeld.py
"""
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from patronen import detect_patronen  # noqa: E402

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "pii-patronen.json"

# Categorieen uit de fixture die deze implementatie niet kent. Leeg: patronen.py dekt
# alle categorieen die de fixture nu bevat (bsn, iban, email, postcode, telefoon, kvk,
# fg, ipv4, ruis).
NIET_ONDERSTEUND: set[str] = set()

# Gevallen waarin patronen.py de norm uit de fixture bewust of bekend NIET haalt.
# De fixture blijft de norm; hier staat wat deze implementatie in plaats daarvan doet,
# zodat de afwijking zichtbaar is en een stille verschuiving toch de test breekt.
# id -> (gevonden waarden na normalisatie, reden)
BEKENDE_AFWIJKINGEN: dict[str, tuple[list[str], str]] = {
    "bsn-08": (["000000000"],
               "de telefoon-regex (0 plus acht tot tien cijfers) pakt de nullenreeks als "
               "telefoonnummer; de BSN-uitsluiting zelf werkt wel"),
    "bsn-09": ([],
               "de BSN-kandidaat eist negen aaneengesloten cijfers; een gespreid geschreven "
               "BSN wordt gemist"),
    "iban-04": (["NL03ABNA0123456789"],
                "geen mod-97-controle, alleen een vormcheck (NL + 2 cijfers + 4 letters + "
                "10 cijfers); publicatiescan valideert wel"),
}


def _norm(waarde: str) -> str:
    """Spaties en koppeltekens weg, zodat '06-12345678' en '06 12345678' gelijk zijn."""
    return re.sub(r"[\s-]", "", waarde)


def _laad_gevallen() -> list[dict]:
    with FIXTURE.open(encoding="utf-8") as f:
        return json.load(f)["gevallen"]


GEVALLEN = _laad_gevallen()


def _gevonden(tekst: str) -> list[str]:
    _, entiteiten = detect_patronen(tekst)
    return sorted({_norm(e["tekst"]) for e in entiteiten})


@pytest.mark.parametrize("geval", GEVALLEN, ids=[g["id"] for g in GEVALLEN])
def test_fixture_geval(geval: dict):
    if geval["categorie"] in NIET_ONDERSTEUND:
        pytest.skip(f"categorie {geval['categorie']!r} niet ondersteund in patronen.py")

    gevonden = _gevonden(geval["tekst"])
    verwacht = sorted({_norm(v) for v in geval["verwacht"]})

    if geval["id"] in BEKENDE_AFWIJKINGEN:
        afwijking, reden = BEKENDE_AFWIJKINGEN[geval["id"]]
        assert sorted(afwijking) != verwacht, (
            f"{geval['id']}: afwijking is gelijk aan de norm, haal 'm uit BEKENDE_AFWIJKINGEN"
        )
        assert gevonden == sorted(afwijking), (
            f"{geval['id']}: bekende afwijking veranderd ({reden}); "
            f"norm={verwacht}, vastgelegd={sorted(afwijking)}, nu={gevonden}"
        )
        return

    assert gevonden == verwacht, f"{geval['id']} ({geval['toelichting']}): {geval['tekst']!r}"


def test_fixture_is_gezond():
    ids = [g["id"] for g in GEVALLEN]
    assert len(ids) == len(set(ids)), "dubbele id in fixture"
    for g in GEVALLEN:
        assert set(g) == {"id", "categorie", "tekst", "verwacht", "toelichting"}, g["id"]
        for v in g["verwacht"]:
            assert v in g["tekst"], f"{g['id']}: verwachte waarde {v!r} staat niet in de tekst"
    onbekend = set(BEKENDE_AFWIJKINGEN) - set(ids)
    assert not onbekend, f"BEKENDE_AFWIJKINGEN verwijst naar onbekende ids: {onbekend}"
