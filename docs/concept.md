# anonimizer — Concept

> Verlaag de drempel om interne kennis te delen door documenten te ontdoen van persoonsgegevens, organisatienamen en andere identificerende informatie.

---

## Het probleem

CISO's en ISO's hebben waardevolle kennis: beleidsnotities, risicoanalyses, aanpakken, trainingsmateriaal, rapportages. Maar die kennis delen ze niet — niet omdat ze het niet willen, maar omdat elk document doorspekt is met namen, afdelingen, interne projectnamen en verwijzingen die niet publiek horen.

Het gevolg: kennis blijft opgesloten in individuele organisaties. De commons blijft leeg.

De anonimizer lost dit op. Niet door mensen te vragen het handmatig te doen (te arbeidsintensief), maar door AI de detectie en suggesties te laten doen — en de mens te laten beslissen.

---

## Wat het doet

```
Document in (pdf, docx, pptx, xlsx, md, txt, html)
    ↓
Laag 1: standaard-vervangingen (altijd stil, geen prompt)
         bijv. "Leiden" → "VOORBEELDGEMEENTE"
    ↓
Laag 2: eerder bevestigde vervangingen uit geheugen (stil)
    ↓
Laag 3: AI detecteert nieuwe entiteiten — namen, e-mails,
         organisaties, projectnamen, interne nummers
    ↓
Per nieuw element: AI-suggestie voor vervanging
                   + jij bevestigt, past aan, of slaat over
    ↓
Geanonimiseerd document uit (.md + .html)
```

**Voorbeelden van vervangingen:**

| Origineel | Suggestie | Jij kiest |
|-----------|-----------|-----------|
| Jan de Vries | de CISO | bevestigen / aanpassen |
| Leiden | VOORBEELDGEMEENTE | automatisch (standaard) |
| j.devries@gemeentex.nl | [e-mailadres verwijderd] | bevestigen / aanpassen |
| het programma X | het weerbaarheidsprogramma | bevestigen / aanpassen |

---

## Interactiemodel

De anonimizer is **interactief, niet blind**. Elk nieuw gedetecteerd element wordt voorgelegd:

```
[1/8] Persoon: "Jan de Vries"
      Suggestie: "de CISO"
      > (Enter = akkoord, eigen tekst = alternatief, s = overslaan, q = stop)
```

Eenmaal bevestigde vervangingen worden onthouden in `memory.json`. Bij een volgend document worden ze automatisch toegepast — geen prompt meer.

---

## Input-formaten

| Formaat | Ondersteuning |
|---------|--------------|
| Plain text (.txt) | Fase 1 |
| Markdown (.md) | Fase 1 |
| HTML (.html, .htm) | Fase 1 |
| Word (.docx) | Fase 1 |
| PDF (tekst-extractie) | Fase 1 |
| PowerPoint (.pptx) | Fase 1 |
| Excel (.xlsx) | Fase 1 |

Afbeeldingen (logo's, covers) worden verwijderd en vervangen door `[AFBEELDING VERWIJDERD]`.

**Output:** altijd zowel `.md` als `.html`.

---

## Technische richting

**Detectie (3 lagen):**
1. Standaard-vervangingen uit `standaard.yaml` — configureerbaar per organisatie, altijd stil
2. Geleerd geheugen uit `memory.json` — vorige sessies onthouden
3. LLM-gestuurde Named Entity Recognition — contextafhankelijk, voor alles wat nog niet bekend is

**Model:** lokaal via Ollama of EU-gehoste API (Mistral). Geen data buiten de EU.

**Output:** gestructureerde Markdown + HTML, klaar voor publicatie in de kennisbank.

---

## Interface

**CLI**

```bash
# Een document
python anonimizer.py verwerk document.pdf

# Hele map
python anonimizer.py verwerk map/ --batch
```

---

## CI-integratie: adviserende privacy scan

De kennisbank bevat een GitHub Action die bij elke Pull Request de ingediende `.md`-bestanden scant met dezelfde LLM-detector. De action **blokkeert nooit** — ze plaatst een adviserende comment voor de reviewer:

> "Let bij het reviewen op regel 42 ('het BRP-project') en regel 105 ('Contactpersoon R. Visser')."

Dit is bewust in lijn met het principe: **AI altijd adviserend, mens beslist.**

---

## Status

Fase 1 — CLI voor alle gangbare documentformaten (.pdf, .docx, .pptx, .xlsx, .md, .txt, .html).
Fase 2 voegt een web UI toe voor niet-technische gebruikers.

Bijdragen welkom — zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md).
