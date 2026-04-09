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
Document in
    ↓
AI detecteert: namen, organisaties, e-mailadressen,
               interne projectnamen, locaties, paden
    ↓
Per element: AI-suggestie voor vervanging
             + jij bevestigt, past aan, of slaat over
    ↓
Geanonimiseerd document uit
```

**Voorbeelden van vervangingen:**

| Origineel | Suggestie | Jij kiest |
|-----------|-----------|-----------|
| Bas Stevens | de CISO | bevestigen / aanpassen |
| Gemeente Leiden | de gemeente | bevestigen / aanpassen |
| f.splinter@leiden.nl | [e-mailadres verwijderd] | bevestigen / aanpassen |
| Programma MWeV | het weerbaarheidsprogramma | bevestigen / aanpassen |
| C:\Users\Bas.Stevens\... | [pad verwijderd] | bevestigen / aanpassen |

---

## Interactiemodel

De anonimizer is **interactief, niet blind**. Elk gedetecteerd element wordt voorgelegd:

```
[1/12] Gevonden: "Bas Stevens"
       Suggestie: "de CISO"
       > (Enter = akkoord, typ alternatief, s = overslaan, q = stop)
```

Dit is bewust. Een batch-vervanging die je niet controleert, is een vervanging die je niet vertrouwt. De mens blijft in de loop.

---

## Input-formaten

| Formaat | Ondersteuning |
|---------|--------------|
| Plain text (.txt) | Fase 1 |
| Markdown (.md) | Fase 1 |
| Word (.docx) | Fase 2 |
| PDF (tekst-extractie) | Fase 2 |

---

## Technische richting

**Detectie:** LLM-gestuurde Named Entity Recognition (NER). Het model identificeert niet alleen namen en e-mailadressen, maar ook contextafhankelijke elementen als interne projectnamen en afdelingsnamen die een regex nooit zou vinden.

**Suggesties:** hetzelfde model stelt een neutrale vervanging voor op basis van context. "Bas Stevens" wordt "de CISO" omdat de context aangeeft dat hij CISO is — niet omdat er een vaste regel is.

**Output:** gestructureerde diff (JSON) van origineel naar geanonimiseerd. Dit maakt het mogelijk om de vervangingen te reviewen, te exporteren, en eventueel opnieuw toe te passen op een bijgewerkt document.

**Model:** lokaal via Ollama of EU-gehoste API. Geen data buiten de EU.

---

## Interface

**Fase 1: CLI**

Laagste drempel voor technische bijdragers. Werkt op elk systeem met Python.

```bash
anonimizer verwerk document.md
anonimizer verwerk --batch map/
```

**Fase 2: Web UI**

Voor niet-technische gebruikers (beleidsmedewerkers, communicatieadviseurs). Upload, klik door de suggesties, download het resultaat.

---

## Integratie met de kennisbank

Na anonimisering kan het document direct worden toegevoegd aan de kennisbank van security-commons-nl. De anonimizer kent de mapstructuur (`security/`, `privacy/`, `bcm/`, `overig/`) en stelt een bestemmingsmap voor op basis van de inhoud.

---

## Status

Concept-fase. Er is nog geen werkende implementatie.

Bijdragen welkom — zowel aan de technische uitwerking (NER-aanpak, CLI-interface, model-keuze) als aan testdocumenten en use cases.

Zie [CONTRIBUTING.md](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md).
