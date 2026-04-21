"""Unit tests voor memory-conflictdetectie (Fase D4)."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from memory import detecteer_conflicten


def _rep(tekst, vervanging, categorie="overig"):
    return {"tekst": tekst, "vervanging": vervanging, "categorie": categorie}


class TestConflictDetectie:
    def test_geen_conflicten(self):
        mem = [_rep("Jan Pietersen", "[persoon]")]
        std = {"Gemeente Leiden": "VOORBEELDGEMEENTE"}
        assert detecteer_conflicten(mem, std) == []

    def test_dubbele_key_met_verschillende_waarde(self):
        mem = [_rep("AVG", "de Algemene Verordening")]
        std = {"AVG": "[wet]"}
        result = detecteer_conflicten(mem, std)
        assert len(result) == 1
        assert result[0]["type"] == "dubbele_key"
        assert result[0]["key"] == "AVG"

    def test_dubbele_key_zelfde_waarde_geen_conflict(self):
        mem = [_rep("CISO", "de CISO")]
        std = {"CISO": "de CISO"}
        # Zelfde vervanging = geen conflict
        result = [c for c in detecteer_conflicten(mem, std) if c["type"] == "dubbele_key"]
        assert result == []

    def test_substring_detectie(self):
        mem = [_rep("Leiden", "X"), _rep("Gemeente Leiden", "Y")]
        std = {}
        result = [c for c in detecteer_conflicten(mem, std) if c["type"] == "substring"]
        assert len(result) == 1
        assert result[0]["kort"] == "Leiden"
        assert result[0]["lang"] == "Gemeente Leiden"

    def test_mojibake_detectie_fffd(self):
        mem = [_rep("Henri�tte", "[persoon]")]
        std = {}
        result = [c for c in detecteer_conflicten(mem, std) if c["type"] == "mojibake"]
        assert len(result) == 1

    def test_mojibake_detectie_dubbele_utf8(self):
        mem = [_rep("InitiÃ«le opzet", "[...]")]
        std = {}
        result = [c for c in detecteer_conflicten(mem, std) if c["type"] == "mojibake"]
        assert len(result) == 1

    def test_te_korte_keys_geen_substring(self):
        # Keys van <3 tekens worden niet op substring getest
        mem = [_rep("FG", "X"), _rep("FGtest", "Y")]
        std = {}
        result = [c for c in detecteer_conflicten(mem, std) if c["type"] == "substring"]
        assert result == []
