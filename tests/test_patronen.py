"""Unit tests voor patronen.py — de deterministische regex-detectielaag.

Draaien: pytest tests/test_patronen.py
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from patronen import detect_patronen, _is_geldig_bsn


def _gevonden(tekst: str, categorie: str | None = None) -> list[str]:
    """Helper: geef lijst gevonden tekstwaarden (optioneel gefilterd op categorie)."""
    _, ent = detect_patronen(tekst)
    if categorie:
        return [e["tekst"] for e in ent if e["categorie"] == categorie]
    return [e["tekst"] for e in ent]


# --- Email -----------------------------------------------------------------

class TestEmail:
    def test_basis(self):
        assert _gevonden("Mail: jan@voorbeeld.nl.", "email") == ["jan@voorbeeld.nl"]

    def test_meerdere(self):
        r = _gevonden("a@b.nl en c.d@e-f.co.uk", "email")
        assert "a@b.nl" in r and "c.d@e-f.co.uk" in r

    def test_hoofdletters(self):
        assert _gevonden("Info@IBDGemeenten.nl", "email") == ["Info@IBDGemeenten.nl"]

    def test_geen_match_zonder_at(self):
        assert _gevonden("voorbeeld.nl is geen email", "email") == []


# --- Telefoon --------------------------------------------------------------

class TestTelefoon:
    @pytest.mark.parametrize("tekst", [
        "070 373 80 11",
        "06-12345678",
        "+31 6 12345678",
        "+31 (0)20 1234567",
        "010-1234567",
        "0205551234",
    ])
    def test_valide_varianten(self, tekst):
        assert _gevonden(tekst, "telefoon"), f"{tekst!r} zou moeten matchen"

    @pytest.mark.parametrize("tekst", [
        "27-12-2022",           # datum
        "v1.0 0.5",             # versies
        "1234567890123",        # te lang
        "2021-2024",            # periode
    ])
    def test_geen_match(self, tekst):
        assert _gevonden(tekst, "telefoon") == [], f"{tekst!r} mag niet matchen"


# --- Postcode --------------------------------------------------------------

class TestPostcode:
    def test_met_spatie(self):
        assert _gevonden("Adres: 2514 JS Den Haag", "locatie") == ["2514 JS"]

    def test_zonder_spatie(self):
        assert _gevonden("2514JS", "locatie") == ["2514JS"]

    def test_geen_kleine_letters(self):
        assert _gevonden("2514 js", "locatie") == []

    def test_begint_niet_met_0(self):
        assert _gevonden("0514 AB", "locatie") == []


# --- KVK -------------------------------------------------------------------

class TestKVK:
    def test_basis(self):
        assert "KVK 27364192" in _gevonden("KVK 27364192")

    def test_met_dubbele_spatie(self):
        assert "KVK  27364192" in _gevonden("KVK  27364192")

    def test_met_dubbelepunt(self):
        assert "KVK: 27364192" in _gevonden("KVK: 27364192")

    def test_case_insensitive(self):
        assert _gevonden("kvk 27364192")

    def test_exact_8_cijfers(self):
        assert not _gevonden("KVK 1234567")   # 7 cijfers
        assert not _gevonden("KVK 123456789") # 9 cijfers


# --- FG-nummer (AP-register) -----------------------------------------------

class TestFG:
    def test_basis(self):
        assert "FG 000424" in _gevonden("FG 000424 Gemeente Leiden")

    def test_geen_match_bij_FG_zonder_nummer(self):
        # "FG" als rol-afkorting mag niet matchen zonder cijfers
        assert _gevonden("De FG is verantwoordelijk", "nummer") == []


# --- IBAN ------------------------------------------------------------------

class TestIBAN:
    def test_nl_met_spaties(self):
        assert "NL91 ABNA 0417 1643 00" in _gevonden("NL91 ABNA 0417 1643 00")

    def test_nl_zonder_spaties(self):
        assert "NL91ABNA0417164300" in _gevonden("NL91ABNA0417164300")

    def test_wrong_country(self):
        assert _gevonden("DE91ABNA0417164300", "nummer") == []


# --- BSN -------------------------------------------------------------------

class TestBSN:
    @pytest.mark.parametrize("geldig", [
        "111222333",
        "123456782",
    ])
    def test_geldig_bsn_via_11_proef(self, geldig):
        assert _is_geldig_bsn(geldig), f"{geldig} moet volgens 11-proef geldig zijn"
        assert geldig in _gevonden(f"BSN: {geldig}")

    @pytest.mark.parametrize("ongeldig", [
        "000000000",    # all zeros
        "111111111",    # faalt 11-proef
        "123456789",    # faalt 11-proef
    ])
    def test_ongeldig_bsn(self, ongeldig):
        assert not _is_geldig_bsn(ongeldig)

    def test_niet_deel_van_telefoon(self):
        # 06-nummer van 10 cijfers mag niet als BSN worden gezien
        r = _gevonden("06 12345678")
        assert not any(e == "612345678" for e in r)


# --- IPv4 ------------------------------------------------------------------

class TestIPv4:
    def test_echte_ip(self):
        assert "192.168.1.1" in _gevonden("Server 192.168.1.1")

    @pytest.mark.parametrize("tekst", [
        "Hoofdstuk 14.2.7.1",
        "Versie 1.2.3.4",
        "sectie 1.1.1.1",
        "norm 10.1.2.3",
    ])
    def test_versienummer_geen_ip(self, tekst):
        """IPs waarbij geen octet >=100 is zijn waarschijnlijk versienummers."""
        assert "[IP-adres verwijderd]" not in str(_gevonden(tekst)), tekst

    def test_ip_met_hoog_octet(self):
        assert "10.0.100.5" in _gevonden("IP 10.0.100.5")
        assert "255.255.255.0" in _gevonden("255.255.255.0")


# --- Overlap-preventie -----------------------------------------------------

class TestGeenOverlap:
    def test_iban_staart_niet_als_telefoon(self):
        """De cijferstaart van een IBAN mag niet apart als telefoon matchen."""
        _, ent = detect_patronen("Rekening NL91 ABNA 0417 1643 00 ok")
        teksten = [e["tekst"] for e in ent]
        assert "NL91 ABNA 0417 1643 00" in teksten
        # Geen telefoon-match op de cijferstaart
        assert not any(e["categorie"] == "telefoon" for e in ent)

    def test_kvk_niet_als_bsn(self):
        """Een KVK-nummer van 8 cijfers mag niet apart als BSN matchen."""
        _, ent = detect_patronen("KVK 27364192 is het nummer")
        # KVK moet gematched zijn, BSN niet
        assert any(e["suggestie"] == "[KVK-nummer verwijderd]" for e in ent)
        assert not any(e["suggestie"] == "[BSN verwijderd]" for e in ent)


# --- Integratie: geen false positives op courante tekst --------------------

class TestGeenFalsePositives:
    """Realistische tekstfragmenten die GEEN detecties mogen opleveren."""

    @pytest.mark.parametrize("tekst", [
        "Versie 1.1 Definitief 4 maart 2025",
        "Hoofdstuk 2.3 Beheer van informatie",
        "De CISO is verantwoordelijk voor informatiebeveiliging.",
        "Pagina 3 van 12",
        "Artikel 33a lid 7",
    ])
    def test_geen_detectie(self, tekst):
        _, ent = detect_patronen(tekst)
        assert ent == [], f"Onverwachte detectie in {tekst!r}: {ent}"
