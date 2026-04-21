# anonimizer

> Verwijder persoonsgegevens en organisatiespecifieke informatie uit documenten — interactief, transparant, EU-soeverein.

Gebouwd zodat CISO's en ISO's interne kennis kunnen delen via de [kennisbank](https://github.com/security-commons-nl/kennisbank) zonder privacyrisico's.

> **Nieuw hier?** Lees de [handleiding](docs/handleiding.md) — stap-voor-stap gids met voorbeelden, redactionele keuzes en troubleshooting.

---

## Wat het doet

Je geeft een document op (PDF, Word, PowerPoint, Excel, Markdown, HTML). De tool:

1. Haalt de tekst eruit en verwijdert afbeeldingen
2. Past automatisch bekende vervangingen toe (bijv. jouw gemeentenaam → `VOORBEELDGEMEENTE`)
3. Laat je per nieuw gevonden naam, e-mailadres of interne term zelf kiezen wat ermee gebeurt
4. Onthoudt jouw keuzes voor de volgende keer
5. Slaat het resultaat op als `.md` én `.html`

---

## Installatie

### 1. Vereisten

- Python 3.11 of nieuwer — [python.org/downloads](https://www.python.org/downloads/)
- Git — [git-scm.com](https://git-scm.com/)

### 2. Haal de code op

```bash
git clone https://github.com/security-commons-nl/anonimizer.git
cd anonimizer
pip install -r requirements.txt
```

### 3. Maak een API-sleutel aan

De tool gebruikt een taalmodel (Mistral) om namen en organisaties te herkennen. Je hebt hiervoor een gratis account nodig:

1. Ga naar [console.mistral.ai](https://console.mistral.ai/)
2. Maak een account aan
3. Ga naar **API Keys** en klik **Create new key**
4. Kopieer de sleutel

### 4. Stel de sleutel in

```bash
cp .env.example .env
```

Open `.env` in een teksteditor en vul je sleutel in:

```
AI_API_KEY=jouw-sleutel-hier
```

### 5. Stel standaard-vervangingen in (optioneel maar aanbevolen)

```bash
cp standaard.yaml.example standaard.yaml
```

Open `standaard.yaml` en pas de namen aan voor jouw organisatie. Alles wat hier staat wordt automatisch vervangen zonder dat je er per keer naar gevraagd wordt.

---

## Gebruik

```bash
# Eén document
python anonimizer.py verwerk document.pdf

# Word-bestand
python anonimizer.py verwerk beleid.docx

# Hele map
python anonimizer.py verwerk map/ --batch

# Met opgegeven uitvoernaam
python anonimizer.py verwerk document.pdf --output schoon.md
```

### Ondersteunde formaten

| Formaat | Extensie |
|---------|----------|
| PDF | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Excel | `.xlsx` |
| Markdown | `.md` |
| Platte tekst | `.txt` |
| HTML | `.html`, `.htm` |

### Interactie

Per nieuw gevonden element kies je wat er mee gebeurt:

```
[1/8] Persoon: "Jan de Vries"
      Suggestie: "de CISO"
      > (Enter = akkoord, eigen tekst = jouw vervanging, s = overslaan, q = stop)
```

Bevestigde keuzes worden onthouden in `memory.json`. De volgende keer dat je een document verwerkt worden ze automatisch toegepast.

---

## Configuratie

### `.env` — API-instellingen

| Variabele | Standaard | Beschrijving |
|-----------|-----------|--------------|
| `AI_API_BASE` | `https://api.mistral.ai/v1` | LLM API-endpoint |
| `AI_API_KEY` | — | API-sleutel (verplicht) |
| `AI_MODEL_NAME` | `mistral-small-latest` | Taalmodel |

Volledig lokaal draaien via Ollama: stel `AI_API_BASE=http://localhost:11434/v1` en `AI_API_KEY=ollama` in.

### `standaard.yaml` — altijd-toepassen vervangingen

Vervangingen die je hier opneemt worden zonder prompt toegepast op elk document. Zie `standaard.yaml.example` voor een startpunt met gangbare gemeente- en regionamen.

### `memory.json` — geleerd geheugen

Wordt automatisch aangemaakt. Bevat alle eerder bevestigde vervangingen. Niet in git — lokaal per gebruiker.

---

## Meer documentatie

- [Handleiding](docs/handleiding.md) — stap-voor-stap gids voor CISO's en ISO's
- [Concept en ontwerp](docs/concept.md)
- [Bijdragen](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md)

---

## Principes

Dit project volgt de [architectuur- en communityprincipes](https://github.com/security-commons-nl/.github/blob/main/PRINCIPLES.md) van security-commons-nl: EU-soevereiniteit, AI altijd adviserend, auditbaarheid by design, least privilege en open source als standaard.
