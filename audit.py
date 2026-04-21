"""Audit-trail logger voor anonimizer.

Schrijft per vervanging één JSONL-regel zodat achteraf traceerbaar is
welke laag welk woord heeft vervangen. Past bij het 'auditbaar by design'
principe van security-commons-nl.

Gebruik (in anonimizer.py):
    logger = AuditLog("audit.jsonl")
    logger.log(pad, origineel, vervanging, bron)
    logger.sluit()
"""
import json
import pathlib
from datetime import datetime, timezone
from typing import IO


class AuditLog:
    """Minimalistische JSONL-logger. Één regel per gelogde gebeurtenis."""

    def __init__(self, pad: pathlib.Path | str):
        self._pad = pathlib.Path(pad)
        self._bestand: IO | None = None

    def _open(self) -> IO:
        if self._bestand is None:
            self._bestand = self._pad.open("a", encoding="utf-8")
        return self._bestand

    def log(
        self,
        document: str,
        origineel: str,
        vervanging: str,
        bron: str,
        categorie: str = "",
    ) -> None:
        """Schrijf één audit-regel."""
        regel = {
            "tijdstip": datetime.now(timezone.utc).isoformat(),
            "document": str(document),
            "origineel": origineel,
            "vervanging": vervanging,
            "bron": bron,
            "categorie": categorie,
        }
        f = self._open()
        f.write(json.dumps(regel, ensure_ascii=False) + "\n")
        f.flush()

    def sluit(self) -> None:
        if self._bestand is not None:
            self._bestand.close()
            self._bestand = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.sluit()
