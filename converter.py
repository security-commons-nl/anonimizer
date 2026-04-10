"""Convert various input formats to clean markdown text."""
import pathlib
import re
from html.parser import HTMLParser


class _HTMLToMarkdown(HTMLParser):
    """Simple HTML to Markdown converter."""

    BLOCK_TAGS = {"p", "div", "section", "article", "main", "header", "footer", "li", "tr"}
    SKIP_TAGS = {"script", "style", "nav", "head"}
    HEADING_TAGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}

    def __init__(self):
        super().__init__()
        self.result = []
        self._skip = 0
        self._in_heading = None
        self._in_bold = False
        self._in_italic = False
        self._in_li = False
        self._in_pre = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return
        if tag in self.HEADING_TAGS:
            self._in_heading = self.HEADING_TAGS[tag]
            self.result.append(f"\n{self._in_heading} ")
        elif tag == "br":
            self.result.append("\n")
        elif tag in ("b", "strong"):
            self._in_bold = True
            self.result.append("**")
        elif tag in ("i", "em"):
            self._in_italic = True
            self.result.append("_")
        elif tag == "li":
            self._in_li = True
            self.result.append("\n- ")
        elif tag == "pre":
            self._in_pre = True
            self.result.append("\n```\n")
        elif tag in self.BLOCK_TAGS:
            self.result.append("\n")
        elif tag == "a":
            attrs_dict = dict(attrs)
            if "href" in attrs_dict:
                self.result.append("[")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag in self.HEADING_TAGS:
            self._in_heading = None
            self.result.append("\n")
        elif tag in ("b", "strong"):
            self._in_bold = False
            self.result.append("**")
        elif tag in ("i", "em"):
            self._in_italic = False
            self.result.append("_")
        elif tag == "li":
            self._in_li = False
        elif tag == "pre":
            self._in_pre = False
            self.result.append("\n```\n")
        elif tag in self.BLOCK_TAGS:
            self.result.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        self.result.append(data)

    def get_markdown(self):
        md = "".join(self.result)
        # Collapse 3+ newlines to 2
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip()


def html_to_markdown(html: str) -> str:
    parser = _HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


ONDERSTEUNDE_EXTENSIES = {".md", ".txt", ".html", ".htm", ".docx", ".pdf", ".pptx", ".xlsx"}


def to_markdown(pad: pathlib.Path) -> str:
    """Read a file and return its content as markdown text."""
    suffix = pad.suffix.lower()

    if suffix in (".html", ".htm"):
        tekst = pad.read_text(encoding="utf-8", errors="replace")
        return html_to_markdown(tekst)

    elif suffix in (".md", ".txt"):
        return pad.read_text(encoding="utf-8", errors="replace")

    elif suffix == ".pdf":
        from converters.pdf import pdf_to_markdown
        return pdf_to_markdown(pad)

    elif suffix == ".docx":
        from converters.docx import docx_to_markdown
        return docx_to_markdown(pad)

    elif suffix == ".pptx":
        from converters.pptx import pptx_to_markdown
        return pptx_to_markdown(pad)

    elif suffix == ".xlsx":
        from converters.xlsx import xlsx_to_markdown
        return xlsx_to_markdown(pad)

    else:
        raise ValueError(
            f"Niet-ondersteund bestandsformaat: {suffix}. "
            f"Ondersteund: {', '.join(sorted(ONDERSTEUNDE_EXTENSIES))}"
        )
