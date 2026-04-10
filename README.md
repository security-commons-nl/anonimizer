# anonimizer

> Verwijder persoonsgegevens en organisatiespecifieke informatie uit documenten — interactief, transparant, EU-soeverein.

Gebouwd zodat CISO's en ISO's interne kennis kunnen delen via de [kennisbank](https://github.com/security-commons-nl/kennisbank) zonder privacyrisico's.

---

## Installatie

```bash
git clone https://github.com/security-commons-nl/anonimizer.git
cd anonimizer
pip install -r requirements.txt
cp .env.example .env   # vul AI_API_KEY in
```

## Gebruik

```bash
# Eén document
python anonimizer.py verwerk document.md

# Met opgegeven uitvoerbestand
python anonimizer.py verwerk document.md --output schoon.md

# Hele map
python anonimizer.py verwerk map/ --batch
```

De tool detecteert automatisch namen, e-mailadressen, organisatienamen en interne projectnamen. Per gevonden element kies je:

```
[1/8] Persoon: "Jan de Vries"
      Suggestie: "de CISO"
      > (Enter = akkoord, eigen tekst = alternatief, s = overslaan, q = stop)
```

## Configuratie

Kopieer `.env.example` naar `.env`:

| Variabele | Standaard | Beschrijving |
|-----------|-----------|--------------|
| `AI_API_BASE` | `https://api.mistral.ai/v1` | LLM API-endpoint |
| `AI_API_KEY` | — | API-sleutel |
| `AI_MODEL_NAME` | `mistral-small-latest` | Taalmodel |

Alternatief: volledig lokaal via Ollama (`AI_API_BASE=http://localhost:11434/v1`, `AI_API_KEY=ollama`).

## Meer documentatie

- [Concept en ontwerp](docs/concept.md)
- [Bijdragen](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md)

## Status

Fase 1 — CLI voor `.md` en `.txt` bestanden. Fase 2 voegt Word/PDF en een web UI toe.

---

## Principes

Dit project volgt de [architectuur- en communityprincipes](https://github.com/security-commons-nl/.github/blob/main/PRINCIPLES.md) van security-commons-nl: EU-soevereiniteit, AI altijd adviserend, auditbaarheid by design, least privilege en open source als standaard.
