# Plan: anonimizer — aanscherping voor harde use cases

> Aanvulling op [ROADMAP.md](../ROADMAP.md). Fase 3.5: **detectiekwaliteit** op harde gevallen.

## Uitgangspunten

- Bestaande 3-laagse architectuur (standaard → memory → LLM) blijft intact
- Verbeteringen zijn additief, geen breaking changes
- Elke stap is afzonderlijk meetbaar tegen een ground-truth testset
- Auditbaar by design: zichtbaar welke laag wat matchte
- EU-soeverein: geen nieuwe externe diensten

## De 8 harde gevallen (uit test tegen 7 Leidse-regio-documenten)

| # | Case | Nu | Gewenst |
|---|---|---|---|
| 1 | Gestructureerde IDs (KVK, FG, BSN, IBAN, postcode, telefoon, email) | LLM-afhankelijk, wisselend | Deterministisch 100% |
| 2 | Formulierlabels ("Naam", "Telefoonnummer" als kolomkop, geen waarde) | Risico op over-anonimisering | Blijft staan |
| 3 | Losse voornamen (Khalid, Frank) | Wisselend | Consistent herkend |
| 4 | Niet-Nederlandse achternamen (Errami, IJzerman) | LLM-afhankelijk | Ground-truth validatie |
| 5 | Diacrieten na PDF-extractie (Henriëtte → Henri�tte) | Mojibake in input | Detectie + waarschuwing |
| 6 | Korte afkortingen in standaard.yaml (IB&P, BIO) | Geen word-boundary | Optionele `\b`-wrap |
| 7 | Context-afhankelijke org-namen (IBD/VNG publiek, interne afdeling wél) | Geen onderscheid | Allowlist publieke organisaties |
| 8 | Anaforen (dezelfde persoon later alleen voornaam) | Geen koppeling | Memory linkt voor- en achternaam |

## Fasering

### Fase A — Kwaliteit verifieerbaar maken

Zonder meetlat kun je niet verbeteren.

- **A1**. Ground-truth annotatie: markeer per testdocument alle PII in JSON, inclusief bewuste *niet-anonimiseer*-markeringen
- **A2**. `--dry-run` flag: detectie zonder wegschrijven, JSON-output van alle matches
- **A3**. `evalueer.py`: runt dry-run over testset, vergelijkt met ground-truth, rapporteert precision/recall/F1 per categorie en per laag
- **A4**. CI-integratie: regressie direct zichtbaar

### Fase B — Deterministische regex-laag

Plug de gaten waar LLM's zwak zijn: gestructureerde identifiers.

- **B1**. Nieuwe `patronen.py` met regex-detectors voor e-mail, NL-telefoon, postcode, IP, KVK, FG-AP-nummer, BSN (met 11-proef), IBAN
- **B2**. Integreer als laag 1.5 (tussen standaard en memory): auto-toepasbaar, niet-interactief
- **B3**. Uitbreiden `standaard.yaml.example` met o.a. `leidse-regio.nl` → generiek domein
- **B4**. Memory-sanering: mojibake opruimen + UTF-8 assertion bij load/save

### Fase C — LLM-kwaliteit

- **C1**. Prompt-herziening: formulierlabels behouden, losse voornamen herkennen, NL-achternamen met tussenvoegsels, few-shot voorbeelden uit testset
- **C2**. Chunking voor lange documenten (context-window)
- **C3**. Allowlist publieke organisaties (IBD, VNG, NCSC, AP, BIO)
- **C4**. (Optioneel) zelf-consistency via dubbele LLM-run met union

### Fase D — Robuustheid & audit

- **D1**. Word-boundary `\b` voor keys ≤4 tekens, configureerbaar per regel
- **D2**. PDF-encoding-detector: scan op `�` / mojibake, waarschuw
- **D3**. Audit-trail: per vervanging loggen welke laag, optionele `--audit output.jsonl`
- **D4**. Conflict-detectie in memory+standaard

### Fase E — Contextuele beslissingen

Alleen oppakken als testset na A–D aantoont dat het nodig is.

- **E1**. Anafoor-linking: "Bas Stevens" → "de CISO" ook toepassen op losse "Bas"
- **E2**. Rol-contextualisering: `de [functietitel]` waar functie bekend
- **E3**. Interne/externe organisatie-classifier met user-confirm

## Volgorde & beslismomenten

```
A (fundament) → B (regex) → C (LLM-prompt) → D (robuust) → E (context)
                    ↓             ↓
                    └─ meet ──────┘   na elke fase: evalueer.py draaien
```

**Beslispunt na B+C1**: als recall >0.95 op testset, is E mogelijk overbodig.

## Succescriteria

- Precision/recall ≥ 0.95 / 0.90 op testset
- Geen over-anonimisering van formulierlabels
- Geen false positive op "Leiden" in "Leiderdorp"
- PDF-extractie zonder mojibake voor de 2 PDFs
- Audit-trail traceerbaar

## Buiten scope

- Eigen NER-model trainen
- Database/backend (memory.json blijft lokaal)
- Afbeeldingen/OCR (bestaande roadmap fase 3)
