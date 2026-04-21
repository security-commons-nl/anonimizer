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

## Fase 3.5 — Detectiekwaliteit op harde gevallen

Zie [docs/plan-aanscherping.md](docs/plan-aanscherping.md) voor het volledige plan.

Samenvatting in volgorde van uitvoering:
- **A** — Kwaliteit verifieerbaar maken: ground-truth, `--dry-run`, `evalueer.py`, CI
- **B** — Deterministische regex-laag voor KVK/FG/BSN/IBAN/postcode/telefoon/email
- **C** — LLM-prompt aanscherpen: formulierlabels behouden, losse voornamen, publieke-organisatie-allowlist
- **D** — Robuustheid: word-boundary voor korte keys, PDF-mojibake-detectie, audit-trail per vervanging
- **E** — Contextuele beslissingen: anafoor-linking, rol-contextualisering *(alleen als nodig)*

---

## Fase 3 — Uitbreidingen

- [ ] CI-scanner stabiliseren — robuustere foutafhandeling, betere output bij geen bevindingen
- [ ] Batch-verwerking verbeteren — voortgangsindicator bij grote mappen
- [ ] Ondersteuning voor .odt en .rtf bestanden
- [ ] `--dry-run` vlag — toon detecties zonder te schrijven
- [ ] Integratie met kennisbank-workflow: directe upload na anonimisering

### Afbeeldingen anonimiseren in plaats van verwijderen

Huidige gedrag: alle afbeeldingen worden uit het document gestript en vervangen door `[AFBEELDING VERWIJDERD]`. Daarmee verdwijnt essentiële context — architectuurplaten, processchema's, screenshots die het verhaal dragen zijn onvervangbaar als tekst.

Doel: afbeeldingen **behouden** in de output, maar **inhoudelijk geanonimiseerd**.

- [ ] OCR-laag toevoegen (bv. Tesseract of een EU-gehoste vision-LLM) om tekst uit afbeeldingen te extraheren
- [ ] Geëxtraheerde tekst door dezelfde anonimizer-pipeline als documenttekst (standaard.yaml → memory → LLM NER)
- [ ] Afbeelding **her-renderen** zonder originele inhoud:
  - Diagrammen / flowcharts → **Mermaid** (structuur behouden, tekst vervangen)
  - Eenvoudige schema's en tabellen → **SVG** met geanonimiseerde labels
  - Screenshots van UI's → SVG-mockup of wireframe met generieke labels
  - Foto's van personen → blur of symbolische vervanging (geen rendering)
- [ ] Fallback: als her-rendering niet betrouwbaar kan, val terug op huidige gedrag (strippen) + duidelijke waarschuwing in de output
- [ ] Interactieve review: per afbeelding toont de tool het origineel + de voorgestelde vervanging, gebruiker keurt goed of slaat over

Dit is de grootste waarde-toevoeging voor de kennisbank: documenten met behouden visuele structuur zonder PII-risico.

---

## Bijdragen

Heb je ideeën of wil je bijdragen? Open een [issue](https://github.com/security-commons-nl/anonimizer/issues) of zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md).
