# anonimizer — Roadmap

> CLI-tool om documenten te anonimiseren voor publicatie in de commons.

---

## Huidige staat

De anonimizer is functioneel als CLI-tool met aangescherpte detectiekwaliteit.

**Basis (oorspronkelijke release):**
- Conversie van .pdf, .docx, .pptx, .xlsx, .md, .txt, .html naar markdown
- Drie-laagse detectie: standaard-vervangingen → geheugen → LLM NER (Mistral EU)
- Interactieve bevestigingsloop per entiteit
- Zelf-lerend geheugen (memory.json)
- Dual output: `.md` én `.html` met gestileerde placeholders
- CI-scanner voor GitHub Actions

**Detectiekwaliteit** (uitgewerkt in [docs/plan-aanscherping.md](docs/plan-aanscherping.md)):
- Deterministische regex-laag voor e-mail, telefoon, postcode, IP, KVK, FG-nummer, IBAN, BSN (11-proef)
- LLM-prompt met expliciete niet-detecteren-lijst (formulierlabels, publieke organisaties) en few-shot voorbeelden
- Allowlist-postfilter voor hardnekkige LLM-FPs (CISO/ISO/AVG/IBD/VNG)
- Chunking voor lange documenten (8k tekens, 400 overlap)
- Anafoor-linking: losse voornamen worden gekoppeld aan reeds gedetecteerde volle namen
- DOCX text frames, headers en footers worden nu ook geëxtraheerd

**Robuustheid:**
- Word-boundary voor korte keys (BIO matcht niet in "biografie")
- PDF-mojibake-waarschuwing bij encoding-problemen
- Audit-trail via `--audit output.jsonl`
- Conflict-detectie tussen memory en standaard (dubbele keys, substring, mojibake)
- Memory-sanering via `saneer_memory.py`

**Kwaliteitsborging:**
- 90 unit tests (patronen, replacer, memory, audit, anafoor)
- `evalueer.py` met precision/recall/F1 per document tegen ground-truth
- `--dry-run` flag voor niet-destructieve detectie
- GitHub Actions CI met `--min-precision 1.0` regressie-gate

**Eindmetingen op testset (8 documenten, Leidse regio + synthetisch):**
- offline (regex + standaard): P=1.000  R=0.487  F1=0.655
- met LLM + chunking + anafoor: P=0.970  R=0.821  F1=0.889

---

## Openstaand werk

### Fase 2 — Uitbreidingen en integratie

- [ ] CI-scanner stabiliseren — robuustere foutafhandeling, betere output bij geen bevindingen
- [ ] Batch-verwerking verbeteren — voortgangsindicator bij grote mappen
- [ ] Ondersteuning voor .odt en .rtf bestanden
- [ ] Integratie met kennisbank-workflow: directe upload na anonimisering

### Fase 3 — Afbeeldingen anonimiseren in plaats van verwijderen

Huidige gedrag: alle afbeeldingen worden uit het document gestript en vervangen door `[AFBEELDING VERWIJDERD]`. Daarmee verdwijnt essentiële context — architectuurplaten, processchema's, screenshots die het verhaal dragen zijn onvervangbaar als tekst.

Doel: afbeeldingen **behouden** in de output, maar **inhoudelijk geanonimiseerd**.

- [ ] OCR-laag toevoegen (bv. Tesseract of een EU-gehoste vision-LLM) om tekst uit afbeeldingen te extraheren
- [ ] Geëxtraheerde tekst door dezelfde anonimizer-pipeline als documenttekst (standaard.yaml → patronen → memory → LLM NER)
- [ ] Afbeelding **her-renderen** zonder originele inhoud:
  - Diagrammen / flowcharts → **Mermaid** (structuur behouden, tekst vervangen)
  - Eenvoudige schema's en tabellen → **SVG** met geanonimiseerde labels
  - Screenshots van UI's → SVG-mockup of wireframe met generieke labels
  - Foto's van personen → blur of symbolische vervanging (geen rendering)
- [ ] Fallback: als her-rendering niet betrouwbaar kan, val terug op huidige gedrag (strippen) + duidelijke waarschuwing in de output
- [ ] Interactieve review: per afbeelding toont de tool het origineel + de voorgestelde vervanging, gebruiker keurt goed of slaat over

Dit is de grootste waarde-toevoeging voor de kennisbank: documenten met behouden visuele structuur zonder PII-risico.

### Fase 4 — anonimizer-web

Browser-gebaseerde UI zodat CISO's zonder Python-kennis documenten kunnen anonimiseren.

Zie [anonimizer-web](https://github.com/security-commons-nl/anonimizer-web) voor de roadmap van de webinterface.

---

## Bijdragen

Heb je ideeën of wil je bijdragen? Open een [issue](https://github.com/security-commons-nl/anonimizer/issues) of zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md).
