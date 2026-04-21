"""Unit tests voor audit-trail logger (Fase D3)."""
import sys
import json
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from audit import AuditLog


def test_schrijft_jsonl(tmp_path):
    pad = tmp_path / "audit.jsonl"
    with AuditLog(pad) as log:
        log.log("doc.docx", "Jan", "[persoon]", "llm", "persoon")
        log.log("doc.docx", "leiden", "VOORBEELD", "standaard")

    regels = pad.read_text(encoding="utf-8").splitlines()
    assert len(regels) == 2

    eerste = json.loads(regels[0])
    assert eerste["origineel"] == "Jan"
    assert eerste["vervanging"] == "[persoon]"
    assert eerste["bron"] == "llm"
    assert eerste["categorie"] == "persoon"
    assert eerste["document"] == "doc.docx"
    assert "tijdstip" in eerste


def test_utf8_behouden(tmp_path):
    pad = tmp_path / "audit.jsonl"
    with AuditLog(pad) as log:
        log.log("doc", "Henriëtte", "[persoon]", "llm")
    inhoud = pad.read_text(encoding="utf-8")
    assert "Henriëtte" in inhoud


def test_append_bij_bestaand_bestand(tmp_path):
    pad = tmp_path / "audit.jsonl"
    with AuditLog(pad) as log:
        log.log("a", "X", "Y", "standaard")
    with AuditLog(pad) as log:
        log.log("b", "P", "Q", "patroon")
    regels = pad.read_text(encoding="utf-8").splitlines()
    assert len(regels) == 2
