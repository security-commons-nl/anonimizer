"""Unit tests voor replacer.py — word-boundary gedrag voor korte keys."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from replacer import apply, _is_korte_key


class TestKorteKeyHerkenning:
    @pytest.mark.parametrize("key", ["FG", "BIO", "IB", "CIO", "AVG", "ISO"])
    def test_kort_alfanumeriek_is_kort(self, key):
        assert _is_korte_key(key)

    @pytest.mark.parametrize("key", ["Leiden", "Gemeente Leiden", "Holland Rijnland"])
    def test_lang_is_niet_kort(self, key):
        assert not _is_korte_key(key)

    def test_speciale_tekens_niet_kort(self):
        # IB&P bevat & (geen woordkarakter) op positie 2 — regel zegt:
        # begint en eindigt met \w. "IB&P" begint met I en eindigt met P.
        assert _is_korte_key("IB&P")

    def test_eindigt_op_niet_woord(self):
        assert not _is_korte_key("IB-")


class TestWordBoundaryVoorKorteKeys:
    def test_korte_key_matcht_als_los_woord(self):
        assert apply("De FG is hier.", {"FG": "functionaris"}) == "De functionaris is hier."

    def test_korte_key_matcht_niet_binnen_ander_woord(self):
        # "FG" mag niet matchen in "FGV" of "overFGame"
        result = apply("De FGV en overFGame.", {"FG": "X"})
        assert "FGV" in result
        assert "overFGame" in result

    def test_BIO_niet_in_biografie(self):
        # Kritisch: BIO mag niet matchen in "biografie"
        result = apply("De biografie van BIO", {"BIO": "de Baseline"})
        assert "biografie" in result
        assert "de Baseline" in result

    def test_lange_key_werkt_als_voorheen(self):
        result = apply("Gemeente Leiden is groot", {"Gemeente Leiden": "VOORBEELDGEMEENTE"})
        assert "VOORBEELDGEMEENTE" in result

    def test_case_insensitive_blijft(self):
        result = apply("de fg meldt", {"FG": "functionaris"})
        assert "functionaris" in result

    def test_IB_P_als_los_woord(self):
        # IB&P is geldige korte key (begint/eindigt op woordkarakter)
        result = apply("Team IB&P is betrokken", {"IB&P": "VOORBEELDDIENST"})
        assert "VOORBEELDDIENST" in result


class TestLangereFrase:
    def test_langer_dan_drempel(self):
        # Korte frases met spaties zijn technisch >4 tekens, geen boundary nodig
        result = apply("in de Leidse Regio is het", {"Leidse Regio": "REGIO"})
        assert "REGIO" in result


class TestVolgorde:
    def test_langste_matches_eerst(self):
        # "Gemeente Leiden" moet vóór "Leiden" vervangen worden
        result = apply(
            "Gemeente Leiden in Leiden",
            {"Leiden": "STAD", "Gemeente Leiden": "GEMEENTE"},
        )
        assert "GEMEENTE" in result
        # Na eerste substitutie moet de losse "Leiden" ook vervangen worden
        assert "STAD" in result
