# anonimizer — Roadmap

> CLI-tool om documenten te anonimiseren voor publicatie in de commons.

---

## Huidige staat

De anonimizer is functioneel als CLI-tool.

**Beschikbaar:**
- Conversie van .pdf, .docx, .pptx, .xlsx, .md, .txt, .html naar markdown
- Drie-laagse detectie: standaard-vervangingen → geheugen → LLM NER (Mistral EU)
- Interactieve bevestigingsloop per entiteit
- Zelf-lerend geheugen (memory.json) — bevestigde vervangingen worden onthouden
- Dual output: `.md` én `.html` met gestileerde placeholders
- CI-scanner voor GitHub Actions (adviserende privacy-check op PRs)

---

## Fase 2 — anonimizer-web

Browser-gebaseerde UI zodat CISO's zonder Python-kennis documenten kunnen anonimiseren.

Zie [anonimizer-web](https://github.com/security-commons-nl/anonimizer-web) voor de roadmap van de webinterface.

---

## Fase 3 — Uitbreidingen

- [ ] CI-scanner stabiliseren — robuustere foutafhandeling, betere output bij geen bevindingen
- [ ] Batch-verwerking verbeteren — voortgangsindicator bij grote mappen
- [ ] Ondersteuning voor .odt en .rtf bestanden
- [ ] `--dry-run` vlag — toon detecties zonder te schrijven
- [ ] Integratie met kennisbank-workflow: directe upload na anonimisering

---

## Bijdragen

Heb je ideeën of wil je bijdragen? Open een [issue](https://github.com/security-commons-nl/anonimizer/issues) of zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md).
