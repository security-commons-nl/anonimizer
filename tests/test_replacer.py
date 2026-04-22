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


class TestWordBoundaryVoorLangeKeys:
    """Keys langer dan 4 tekens moeten óók \\b krijgen — anders breken ze
    samenstellingen. Dit was de regressie die 'beveiliging' overal liet
    matchen in 'informatiebeveiliging'."""

    def test_beveiliging_matcht_niet_in_informatiebeveiliging(self):
        result = apply(
            "informatiebeveiliging en fysieke beveiliging",
            {"beveiliging": "de beveiligingsafdeling"},
        )
        assert "informatiebeveiliging" in result
        assert "de beveiligingsafdeling" in result

    def test_leiden_matcht_niet_in_begeleiden(self):
        result = apply(
            "het begeleiden van Leiden",
            {"Leiden": "VOORBEELDGEMEENTE"},
        )
        assert "begeleiden" in result
        assert "VOORBEELDGEMEENTE" in result

    def test_directeur_matcht_niet_in_directeuren(self):
        # 'directeur' mag 'directeuren' niet breken
        result = apply(
            "de directeuren en de directeur",
            {"directeur": "de leidinggevende"},
        )
        assert "directeuren" in result
        assert "de leidinggevende" in result


class TestDubbeleLidwoordenCollapsen:
    """'de CISO' als vervanging en 'de' al in zin → 'de de CISO'. Moet
    gecollapsed worden tot 'de CISO'."""

    def test_de_de_wordt_de(self):
        result = apply(
            "goedgekeurd door de CISO",
            {"CISO": "de Chief Information Security Officer"},
        )
        assert "de de" not in result.lower()
        assert "de Chief Information Security Officer" in result

    def test_het_het_wordt_het(self):
        result = apply(
            "voldoen aan het beleid",
            {"beleid": "het informatiebeveiligingsbeleid"},
        )
        assert "het het" not in result.lower()

    def test_een_een_wordt_een(self):
        result = apply(
            "is een werknemer",
            {"werknemer": "een medewerker"},
        )
        assert "een een" not in result.lower()

    def test_geen_collapse_over_andere_woorden(self):
        # "de grote de auto" is weird input, geen collapse target
        result = apply("de grote auto", {})
        assert result == "de grote auto"


class TestPlaceholderLijstCollapsen:
    """Lijsten van identieke VOORBEELDGEMEENTE-tokens collapsen naar 'de
    betrokken gemeenten'. Gebeurt post-replacement."""

    def test_drie_tokens_komma_gescheiden(self):
        result = apply(
            "de gemeenten Leiden, Leiderdorp, Oegstgeest",
            {"Leiden": "VOORBEELDGEMEENTE", "Leiderdorp": "VOORBEELDGEMEENTE", "Oegstgeest": "VOORBEELDGEMEENTE"},
        )
        assert "VOORBEELDGEMEENTE, VOORBEELDGEMEENTE" not in result
        assert "de betrokken gemeenten" in result

    def test_vier_tokens_met_en(self):
        result = apply(
            "Leiden, Leiderdorp, Oegstgeest en Zoeterwoude",
            {
                "Leiden": "VOORBEELDGEMEENTE", "Leiderdorp": "VOORBEELDGEMEENTE",
                "Oegstgeest": "VOORBEELDGEMEENTE", "Zoeterwoude": "VOORBEELDGEMEENTE",
            },
        )
        assert "de betrokken gemeenten" in result
        assert "VOORBEELDGEMEENTE" not in result

    def test_twee_tokens_met_en(self):
        # Zelfs 2 identieke op rij is informatieverlies — collapse
        result = apply(
            "Leiden en Leiderdorp",
            {"Leiden": "VOORBEELDGEMEENTE", "Leiderdorp": "VOORBEELDGEMEENTE"},
        )
        assert "de betrokken gemeenten" in result

    def test_twee_tokens_met_of(self):
        result = apply(
            "Leiden of Leiderdorp",
            {"Leiden": "VOORBEELDGEMEENTE", "Leiderdorp": "VOORBEELDGEMEENTE"},
        )
        assert "de betrokken gemeenten" in result

    def test_enkele_token_blijft_staan(self):
        # Eén VOORBEELDGEMEENTE in een zin — niet collapsen
        result = apply("alleen Leiden doet mee", {"Leiden": "VOORBEELDGEMEENTE"})
        assert "VOORBEELDGEMEENTE" in result
        assert "de betrokken gemeenten" not in result

    def test_twee_verschillende_placeholders_niet_collapsen(self):
        # VOORBEELDGEMEENTE en VOORBEELDREGIO zijn verschillend
        result = apply(
            "Leiden en Leidse Regio",
            {"Leiden": "VOORBEELDGEMEENTE", "Leidse Regio": "VOORBEELDREGIO"},
        )
        assert "VOORBEELDGEMEENTE" in result
        assert "VOORBEELDREGIO" in result
