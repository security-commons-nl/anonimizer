"""Convert PDF to markdown text. Images are replaced with a placeholder."""
import pathlib
import re
import pypdf


_SKIP_WOORDEN = re.compile(
    r'\b(Concept|Definitief|Status|Versie|Version|Draft|Final)\b', re.IGNORECASE
)


def _is_koptekst_kandidaat(s: str) -> bool:
    """Basisfilters die voor alle koptekst-patronen gelden."""
    if not s or len(s) > 80:
        return False
    if re.search(r'\.{3,}', s):          # inhoudsopgave-stippels
        return False
    if re.search(r'\bPagina\s+\d+', s, re.IGNORECASE):  # paginamarkering
        return False
    if re.search(r'\d{4}', s):           # bevat een jaar → versietabel of datum
        return False
    if _SKIP_WOORDEN.search(s):          # versietabel-woorden
        return False
    return True


_HOOFD = r'[A-Z\u00C0-\u024F]'
_TITEL = r'[\w\s\-&/(),.\u00C0-\u024F]'


def _heading_niveau_genummerd(s: str) -> int | None:
    """Geef niveau voor genummerde en speciaal-opgemaakte secties, of None."""
    if not _is_koptekst_kandidaat(s):
        return None
    # Zinnen eindigen op een punt — dat zijn geen koppen
    if s.endswith('.'):
        return None
    # Genummerd: 1.1.1 Titel
    if re.match(rf'^\d+\.\d+\.\d+\s+{_HOOFD}{_TITEL}{{1,50}}$', s):
        return 4
    # Genummerd: 1.1 Titel
    if re.match(rf'^\d+\.\d+\s+{_HOOFD}{_TITEL}{{1,50}}$', s):
        return 3
    # Genummerd: 1 Titel
    if re.match(rf'^\d+\s+{_HOOFD}{_TITEL}{{1,60}}$', s):
        return 2
    # Artikel-stijl: "Artikel 1 Titel" of "Artikel 1   Titel"
    if re.match(rf'^Artikel\s+\d+\s+{_HOOFD}{_TITEL}{{1,80}}$', s, re.IGNORECASE):
        return 2
    # Volledig hoofdletters (document-titel of hoofdsectie): "REGELING TOEGANGSPAS"
    if re.match(r'^[A-Z][A-Z\s\-&/()]{5,70}$', s) and s == s.upper():
        return 2
    return None


def _add_headings(tekst: str) -> str:
    """Voeg markdown-koptekens toe op basis van patroonherkenning."""
    regels = tekst.split('\n')
    resultaat = []

    for i, regel in enumerate(regels):
        s = regel.strip()

        # Genummerde koppen
        niveau = _heading_niveau_genummerd(s)

        # Ongenummerde koppen: korte regel, begint met hoofdletter,
        # voorafgegaan door lege regel, gevolgd door inhoud
        if niveau is None and _is_koptekst_kandidaat(s):
            if (
                3 <= len(s) <= 50
                and re.match(r'^[A-Z\u00C0-\u024F]', s)
                and not s.endswith('.')
                and not re.search(r'[,;:]', s)
                and not re.search(r'\s{2,}', s)   # geen extra spaties (tabel/TOC)
            ):
                prev_leeg = (i == 0) or not regels[i - 1].strip()
                volgende_heeft_inhoud = (
                    i < len(regels) - 1 and len(regels[i + 1].strip()) > 20
                )
                if prev_leeg and volgende_heeft_inhoud:
                    niveau = 3

        if niveau:
            prefix = '#' * niveau
            resultaat.append(f'\n{prefix} {s}')
        else:
            resultaat.append(regel)

    return '\n'.join(resultaat)


def pdf_to_markdown(pad: pathlib.Path) -> str:
    reader = pypdf.PdfReader(pad)
    parts = []
    for page in reader.pages:
        tekst = (page.extract_text() or "").strip()
        if tekst:
            parts.append(_add_headings(tekst))
        if page.images:
            parts.append("[AFBEELDING VERWIJDERD]")
    return "\n\n".join(parts)
