"""Unit tests voor anafoor-linking (Fase E1)."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from anafoor import vind_anaforen, expand_persoon_mappings, _splits_naam


class TestSplitsNaam:
    def test_twee_termen(self):
        assert _splits_naam("Bas Stevens") == ("Bas", "Stevens")

    def test_drie_termen(self):
        assert _splits_naam("Jan de Vries") == ("Jan", "de Vries")

    def test_losse_voornaam(self):
        assert _splits_naam("Khalid") is None

    def test_lege_string(self):
        assert _splits_naam("") is None


class TestVindAnaforen:
    def test_basis_case(self):
        """Volle naam gedetecteerd; later komt losse voornaam voor."""
        mapping = {"Rudolf Kroes": "de auteur"}
        tekst = "Goedgekeurd door Rudolf Kroes. Rudolf meldt daarna dat..."
        anaforen = vind_anaforen(mapping, tekst)
        assert anaforen == {"Rudolf": "de auteur"}

    def test_geen_standalone_geen_anafoor(self):
        """Als voornaam niet los voorkomt, geen anafoor."""
        mapping = {"Henriëtte Tans": "[persoon]"}
        tekst = "Een memo van Henriëtte Tans aan het bestuur."
        assert vind_anaforen(mapping, tekst) == {}

    def test_ambigu_twee_personen_zelfde_voornaam(self):
        """Als twee personen dezelfde voornaam hebben, skip ambigu geval."""
        mapping = {
            "Jan Pietersen": "[persoon A]",
            "Jan Vermeer": "[persoon B]",
        }
        tekst = "Jan Pietersen en Jan Vermeer werken samen. Jan is project-lead."
        # 'Jan' is ambigu: zou persoon A of B zijn?
        anaforen = vind_anaforen(mapping, tekst)
        assert "Jan" not in anaforen

    def test_common_word_niet_anafoor(self):
        """'Bas' als voornaam wordt overgeslagen omdat het ook een gewoon woord is."""
        # Maar Bas staat op common list → skip. Dus geen anafoor.
        # Testcase: niet alle voornamen zijn common. Gebruik een niet-common.
        mapping = {"Bas Stevens": "de CISO"}
        tekst = "Bas Stevens werkt. De bas-gitaar is van Bas."
        # Ondanks dat Bas later staat, is Bas op common list dus geen anafoor
        assert "Bas" not in vind_anaforen(mapping, tekst)

    def test_niet_common_voornaam(self):
        mapping = {"Rudolf Kroes": "[persoon]"}
        tekst = "De memo door Rudolf Kroes. Eerder had Rudolf al geschreven."
        assert vind_anaforen(mapping, tekst) == {"Rudolf": "[persoon]"}

    def test_te_korte_voornaam(self):
        """Voornamen korter dan MIN_VOORNAAM_LENGTE (3) worden overgeslagen."""
        mapping = {"Ab Errami": "[persoon]"}
        tekst = "Ab Errami was betrokken. Ab kwam ook langs."
        # 'Ab' is 2 tekens, te kort
        assert "Ab" not in vind_anaforen(mapping, tekst)

    def test_word_boundary(self):
        """Voornaam mag niet matchen binnen ander woord."""
        mapping = {"Rudolf Kroes": "[persoon]"}
        # Standalone Rudolf in zin 2, Rudolfweg in zin 3 mag niet matchen
        tekst = "Rudolf Kroes kwam. Later meldde Rudolf dat Rudolfweg 4 het adres is."
        anaforen = vind_anaforen(mapping, tekst)
        assert anaforen == {"Rudolf": "[persoon]"}

    def test_lege_mapping(self):
        assert vind_anaforen({}, "willekeurige tekst") == {}


class TestExpandPersoonMappings:
    def test_integratie(self):
        mappings = {
            "Rudolf Kroes": "[persoon]",
            "leidse-regio.nl": "[e-mail]",
        }
        categorieën = {
            "Rudolf Kroes": "persoon",
            "leidse-regio.nl": "email",
        }
        tekst = "Rudolf Kroes schreef. Rudolf meldt daarna..."
        result = expand_persoon_mappings(mappings, categorieën, tekst)
        assert "Rudolf" in result
        assert result["Rudolf"] == "[persoon]"
        # Originele mappings blijven
        assert result["Rudolf Kroes"] == "[persoon]"
        assert result["leidse-regio.nl"] == "[e-mail]"

    def test_alleen_persoon_categorie(self):
        """Alleen entries met categorie 'persoon' doen mee aan anafoor-zoektocht."""
        mappings = {"Rudolf Kroes": "[x]"}
        categorieën = {"Rudolf Kroes": "organisatie"}  # per ongeluk
        tekst = "Rudolf Kroes. Rudolf ook."
        result = expand_persoon_mappings(mappings, categorieën, tekst)
        # Geen anafoor want categorie is niet persoon
        assert "Rudolf" not in result
