"""Convert PDF to markdown text. Images are replaced with a placeholder."""
import pathlib
import pypdf


def pdf_to_markdown(pad: pathlib.Path) -> str:
    reader = pypdf.PdfReader(pad)
    parts = []
    for page in reader.pages:
        tekst = (page.extract_text() or "").strip()
        if tekst:
            parts.append(tekst)
        if page.images:
            parts.append("[AFBEELDING VERWIJDERD]")
    return "\n\n".join(parts)
