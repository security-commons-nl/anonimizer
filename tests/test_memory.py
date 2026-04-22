"""Unit tests voor memory-conflictdetectie (Fase D4)."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from memory import detecteer_conflicten, valideer_entry, remember


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


class TestValideerEntry:
    """Gate voor toevoeging aan memory. Weigert no-ops, mojibake, en
    generieke lowercase-nouns die substring-cascade veroorzaken."""

    def test_accept_normale_entry(self):
        ok, reden = valideer_entry("Bas Stevens", "de CISO")
        assert ok, reden

    def test_weigert_no_op(self):
        ok, reden = valideer_entry("Privacy Officer", "Privacy Officer")
        assert not ok
        assert "identiek" in reden.lower() or "no-op" in reden.lower()

    def test_weigert_no_op_case_insensitive(self):
        ok, _ = valideer_entry("Directeur", "directeur")
        assert not ok

    def test_weigert_mojibake_in_origineel(self):
        ok, reden = valideer_entry("co�rdinator", "de coördinator")
        assert not ok
        assert "mojibake" in reden.lower()

    def test_weigert_mojibake_in_vervanging(self):
        ok, _ = valideer_entry("coordinator", "de co�rdinator")
        assert not ok

    def test_weigert_generieke_lowercase_noun(self):
        # 'beveiliging' is een samenstellings-basis — substring-cascade
        # garantie als we het in memory laten.
        ok, reden = valideer_entry("beveiliging", "de beveiligingsafdeling")
        assert not ok
        assert "generiek" in reden.lower() or "blocklist" in reden.lower()

    def test_weigert_diverse_generieke_nouns(self):
        for noun in ["directeur", "griffie", "griffier", "college", "directie", "receptie"]:
            ok, _ = valideer_entry(noun, f"de {noun}")
            assert not ok, f"{noun!r} zou geweigerd moeten worden"

    def test_accept_generieke_noun_als_onderdeel_van_frase(self):
        # "De directeur van VOORBEELDGEMEENTE" is wel veilig — frase,
        # geen los woord
        ok, _ = valideer_entry("De directeur van Leiden", "de eindverantwoordelijke")
        assert ok

    def test_weigert_lege_tekst(self):
        ok, _ = valideer_entry("", "iets")
        assert not ok


class TestRememberSkiptInvalid:
    def test_remember_voegt_geen_no_op_toe(self):
        mem = []
        mem = remember("Privacy Officer", "Privacy Officer", "functie", mem)
        assert mem == []

    def test_remember_voegt_geen_blocklist_noun_toe(self):
        mem = []
        mem = remember("beveiliging", "de beveiligingsafdeling", "organisatie", mem)
        assert mem == []

    def test_remember_voegt_geldig_entry_wel_toe(self):
        mem = []
        mem = remember("Bas Stevens", "de CISO", "persoon", mem)
        assert len(mem) == 1
        assert mem[0]["tekst"] == "Bas Stevens"

    def test_remember_update_van_bestaande_entry_behoudt_gedrag(self):
        mem = [{"tekst": "X", "vervanging": "Y", "categorie": "a"}]
        mem = remember("X", "Z", "b", mem)
        assert mem[0]["vervanging"] == "Z"
        assert mem[0]["categorie"] == "b"
