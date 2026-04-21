# Handleiding anonimizer

Praktische gids voor CISO's en ISO's die documenten willen anonimiseren voor de [kennisbank](https://github.com/security-commons-nl/kennisbank) of ander publiek gebruik.

Deze handleiding gaat ervan uit dat je de tool al geïnstalleerd hebt. Zo niet, volg eerst [README.md](../README.md#installatie).

---

## Inhoud

1. [Voor je begint](#voor-je-begint)
2. [Een document stap voor stap](#een-document-stap-voor-stap)
3. [De redactionele keuze — wat vervang ik waarmee?](#de-redactionele-keuze)
4. [Wat gebeurt er met afbeeldingen en layout?](#wat-gebeurt-er-met-afbeeldingen-en-layout)
5. [Output reviewen](#output-reviewen)
6. [Troubleshooting](#troubleshooting)
7. [Van schoon document naar kennisbank-PR](#van-schoon-document-naar-kennisbank-pr)

---

## Voor je begint

**Eenmalig instellen — belangrijk.** De kwaliteit van de anonimizer hangt voor 80% af van hoe goed je `standaard.yaml` hebt ingevuld. Hier zet je alles neer wat in *elk* document van jouw organisatie vervangen moet worden, zonder dat de tool ernaar vraagt.

Open `standaard.yaml` en vul minimaal in:

- Jouw gemeentenaam en alle omliggende gemeenten (mensen noemen ze zonder na te denken)
- Samenwerkingsverbanden (bv. *Holland Rijnland*, *Regio Gooi en Vechtstreek*)
- Interne afdelings-afkortingen (bv. *IB&P*, *DIV*, *ICT*)
- Leveranciers die je intern veel noemt en niet publiek wilt hebben
- Namen van interne systemen en applicaties

Alles wat hier niet in staat, krijg je per document opnieuw voor je neus. Goede investering.

---

## Een document stap voor stap

Stel je wilt een intern memo over incidentresponse anonimiseren.

### 1. Document aanleveren

```bash
python anonimizer.py verwerk memo-incidentresponse.docx
```

De tool:
1. Haalt de tekst eruit (afbeeldingen gaan eruit — ze zijn niet te scannen)
2. Past eerst álle `standaard.yaml`-vervangingen toe, stil
3. Haalt daarna het taalmodel erbij om nieuwe namen, e-mailadressen, organisaties en interne termen op te sporen

### 2. Per gevonden element kies je

```
[1/12] Persoon: "Janneke van der Berg"
       Suggestie: "de privacy officer"
       > (Enter = akkoord, eigen tekst, s = overslaan, q = stop)
```

Je vier opties:

| Keuze | Wanneer |
|---|---|
| **Enter** (suggestie overnemen) | Als de voorgestelde vervanging klopt met de rol van de persoon in het document |
| **Eigen tekst** typen | Als je een betere generieke omschrijving weet, of de suggestie past niet |
| **`s` (overslaan)** | Als het géén persoonsgegeven is (false positive — bv. een plaatsnaam die de AI verkeerd typeerde) |
| **`q` (stop)** | Als je merkt dat je keuzes niet goed zijn en opnieuw wilt beginnen |

### 3. Resultaat

Twee bestanden worden aangemaakt naast het origineel:

- `memo-incidentresponse.md` — Markdown, schoon, geschikt voor de kennisbank
- `memo-incidentresponse.html` — Dezelfde inhoud, visueel leesbaar in de browser voor review

Je keuzes zijn opgeslagen in `memory.json`. Volgende keer dat *Janneke van der Berg* voorkomt in een document krijg je geen prompt meer — ze wordt automatisch *de privacy officer*.

---

## De redactionele keuze

Het moeilijkste zit niet in de tool, maar in wat je típt. Drie categorieën:

### Personen

**Vervang door hun rol in het document, niet door een nietszeggende placeholder.**

| Slecht | Beter |
|---|---|
| `Jan de Vries` → `[PERSOON]` | `Jan de Vries` → `de CISO` |
| `Marieke Bakker` → `XXX` | `Marieke Bakker` → `de functionaris gegevensbescherming` |

Reden: een ander die het document leest moet nog steeds snappen *wie met wie* praat. `[PERSOON 1]` vs `[PERSOON 2]` werkt niet als er drie rollen door elkaar lopen.

**Uitzondering:** als iemand op tien plekken voorkomt en hun rol niet relevant is voor het verhaal, mag je ze generiek houden (`een collega`, `een medewerker`).

### Organisaties

| Situatie | Aanpak |
|---|---|
| Jouw eigen gemeente | Al vervangen via `standaard.yaml` → `VOORBEELDGEMEENTE` |
| Andere gemeente die in het document prominent is | `VOORBEELDGEMEENTE` of `een buurgemeente` — liever niet noemen |
| Leverancier wiens product cruciaal is voor het verhaal | Laat staan als het publieke info is (bv. *Microsoft*, *Axians*). Vervang als het een contractpartij is die je niet publiek wilt noemen |
| Anonieme toeleveranciers | `een leverancier`, `een externe partij` |

### E-mailadressen en telefoonnummers

Altijd vervangen. Standaard-patroon:

- `jan.devries@leiden.nl` → `ciso@voorbeeldgemeente.nl`
- `06-12345678` → `[telefoonnummer]`

### Locaties en dossiernummers

Kritisch — vaak vergeten.

- Adressen: `Stadhuisplein 1` → `[adres hoofdkantoor]`
- Dossiernummers, kenmerken: `Z/24/123456` → `[dossierkenmerk]`
- Datums: meestal laten staan (niet identificerend), tenzij het over een specifiek incident gaat dat herleidbaar is

---

## Wat gebeurt er met afbeeldingen en layout?

**Belangrijk om te weten voor je begint — anders verwacht je iets anders dan je krijgt.**

De tool werkt op **tekst**, niet op beeld. Voor elk ondersteund formaat (PDF, DOCX, PPTX, XLSX) wordt de tekst eruit getrokken en omgezet naar Markdown. Afbeeldingen — elk plaatje, elk logo, elke screenshot, elk diagram — worden **verwijderd** en vervangen door een `[AFBEELDING VERWIJDERD]`-marker in de tekst.

### Wat dat betekent per formaat

| Bronbestand | Wat er gebeurt |
|---|---|
| **PPTX** (PowerPoint) | Volledig ondersteund. Tekst per slide wordt als `## Slide 1`, `## Slide 2`, etc. in Markdown gezet. Titels, bullets en textboxen gaan door de anonimizer. Afbeeldingen, logo's, huisstijl-achtergronden verdwijnen |
| **DOCX** (Word) | Alle tekst (paragrafen, tabellen, koppen) behouden. Afbeeldingen eruit |
| **PDF** | Tekst eruit getrokken. Afbeeldingen eruit — inclusief diagrammen die eigenlijk plaatjes zijn |
| **XLSX** (Excel) | Celinhoud wordt tekst. Geen grafieken, geen opmaak |

### Wat de tool *niet* doet

- ❌ **Geen OCR** — tekst die alléén op een afbeelding staat (bv. een screenshot van een Outlook-venster) wordt dus niet gescand. De afbeelding verdwijnt compleet, inclusief de info erop
- ❌ **Geen logo-verwijdering in het origineel** — als je de originele PPTX met huisstijl wilt delen, moet je zelf in PowerPoint de slide-master aanpassen
- ❌ **Geen achtergrond-scrubbing** — interne templates blijven in het origineel staan
- ❌ **Geen blur of redact op foto's** — persoonsfoto's verdwijnen volledig, ze worden niet onherkenbaar gemaakt
- ❌ **Geen diagram-herkenning** — tekst binnen Visio-achtige diagrammen wordt niet geanonimiseerd

### Wat je zelf moet doen als afbeeldingen belangrijk zijn

Als je document zonder beeldmateriaal onbegrijpelijk wordt (bv. architectuurplaten, screenshots die het verhaal dragen), is dit de volgorde:

1. **Eerst handmatig het origineel schonen:**
   - PowerPoint-template vervangen door iets neutraals
   - Logo's uit slide-master verwijderen
   - Screenshots croppen, blurren of uitknippen tot alleen het relevante deel overblijft
   - Persoonsfoto's verwijderen of vervangen
2. **Dan pas door de anonimizer** voor de tekstuele laag
3. **Voeg de geschoonde afbeeldingen apart toe** aan je kennisbank-PR naast het `.md`-bestand — of verwijs naar ze vanuit de Markdown met `![omschrijving](pad/naar/afbeelding.png)`

**Korte versie:** deze tool is gemaakt om **kennis te delen, niet layout.** Output is altijd kale Markdown. Accepteer dat of bewerk zelf het origineel vóór je hem aanbiedt.

---

## Output reviewen

**Belangrijk: de tool is adviserend. Jij bent eindverantwoordelijk.** Voor je publiceert, loop deze checklist door op het `.md`-bestand:

- [ ] Ctrl+F op je eigen gemeentenaam — geen hits
- [ ] Ctrl+F op namen van collega's die in het document zouden kunnen voorkomen — geen hits
- [ ] Ctrl+F op `@` — alleen generieke adressen
- [ ] Ctrl+F op `06-`, `071-`, `020-` etc. — geen telefoonnummers
- [ ] Ctrl+F op dossierkenmerken (`Z/`, `BB/`, jouw zaaknummer-prefix) — geen hits
- [ ] Snel doorlezen op context — klopt het verhaal nog? Staan er geen namen tussen haakjes of in voetnoten die de tool gemist heeft?
- [ ] Check afbeeldingen die je had — staan daar persoonsgegevens op die je apart moet schrubben? (De tool haalt afbeeldingen eruit, maar jij moet besluiten of je ze geanonimiseerd opnieuw toevoegt)

Als je twijfelt over een passage: laat 'm weg. Kennisbank-bijdragen mogen ingekort zijn.

---

## Troubleshooting

### De AI herkent te weinig

**Symptoom:** je scrolt door het eindbestand en er staan nog namen in die de tool niet vroeg.

**Oorzaken en fixes:**
- Het model is te klein → stel in `.env` een grotere variant in: `AI_MODEL_NAME=mistral-medium-latest`
- De namen staan in een tabel of lijst die slecht uit het document kwam → converteer het document eerst handmatig naar `.md` of `.txt` en verwerk dat
- Het zijn zeer Nederlandse namen die het model niet als persoon herkent → voeg ze toe aan `standaard.yaml` voor volgende keer

### De AI herkent te veel

**Symptoom:** de tool vraagt over elke plaatsnaam, dagteken, of bestandsnaam als ware het een persoon.

**Fix:** druk `s` (overslaan) bij false positives. Deze keuzes worden onthouden in `memory.json` — de tool vraagt dezelfde term niet nog eens.

### Ik heb verkeerde keuzes gemaakt — `memory.json` is vervuild

Verwijder `memory.json` en begin opnieuw:

```bash
rm memory.json
```

Je `standaard.yaml` blijft staan. Alleen de per-documentkeuzes zijn weg.

### Ik wil een bestand opnieuw verwerken

Verwijder de `.md` en `.html` van de vorige run en draai `verwerk` opnieuw:

```bash
rm memo-incidentresponse.md memo-incidentresponse.html
python anonimizer.py verwerk memo-incidentresponse.docx
```

Alle bevestigde keuzes uit `memory.json` worden automatisch opnieuw toegepast — je hoeft alleen nieuwe prompts af te handelen.

### Het taalmodel is niet bereikbaar / rate limit

- Check of `AI_API_KEY` correct in `.env` staat
- Wissel tijdelijk naar een lokaal model via Ollama — zie [README](../README.md#configuratie)

---

## Van schoon document naar kennisbank-PR

Zodra je `.md`-bestand clean is:

1. **Fork** de [kennisbank-repo](https://github.com/security-commons-nl/kennisbank) via de GitHub-knop rechtsboven
2. **Clone** je fork lokaal:
   ```bash
   git clone https://github.com/JOUWNAAM/kennisbank.git
   cd kennisbank
   ```
3. **Zet je bestand in de juiste map:**
   - Informatiebeveiliging → `security/`
   - Privacy / AVG / gegevensbescherming → `privacy/`
   - Bedrijfscontinuïteit → `bcm/`
   - Anders → `overig/`
4. **Bestandsnaam:** beschrijvend, zonder spaties. Bv. `memo-incidentresponse-gemeente.md`
5. **Commit en push:**
   ```bash
   git add security/memo-incidentresponse-gemeente.md
   git commit -m "security: voeg memo incidentresponse toe"
   git push
   ```
6. **Open een pull request** via GitHub. De CI-scanner checkt automatisch op mogelijke privacylekken en geeft advies.
7. **Reageer op feedback.** Maintainers reviewen op anonimisering en plaatsing.

Zie ook [CONTRIBUTING.md](https://github.com/security-commons-nl/kennisbank/blob/main/CONTRIBUTING.md) in de kennisbank-repo.

---

## Vragen of problemen?

- Open een [issue op de anonimizer-repo](https://github.com/security-commons-nl/anonimizer/issues) voor tool-problemen
- Open een [issue op de kennisbank-repo](https://github.com/security-commons-nl/kennisbank/issues) voor vragen over bijdragen
- [Discussions](https://github.com/security-commons-nl/kennisbank/discussions) voor inhoudelijk overleg
