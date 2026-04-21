# Testset — anonimizer

Set van 7 beleidsdocumenten (Leidse Regio) om detectie-kwaliteit te meten.

## Gebruik

```bash
# Snel, zonder LLM:
python evalueer.py testset/ --offline

# Volledig (kost LLM-credits):
python evalueer.py testset/

# JSON-rapport:
python evalueer.py testset/ --offline --json rapport.json
```

## Ground truth

Per document is er een `<bestand>.groundtruth.json` met:

- **`moet_gedetecteerd`**: entiteiten die de tool moet vinden (persoonsnamen, e-mails, KVK, etc.)
- **`moet_niet_gedetecteerd`**: entiteiten die **niet** vervangen mogen worden (formulierlabels, publieke organisatienamen, afkortingen uit officiële tabellen)

Deze annotaties zijn handmatig opgebouwd en mogen uitgebreid worden zodra nieuwe randgevallen opduiken.

## Documenten (niet in git)

De testdocumenten zelf zijn `.gitignore`d — het zijn interne Leiden-stukken. Zet ze hier neer om te draaien:

```
testset/
  ├── Beleid Email en Chat voor Gezondheidsinformatie.docx
  ├── Beleid Strategisch IB-beleid Leidse Regio.pdf
  ├── Beleid Strategisch Privacy Beleid Leidse Regio.pdf
  ├── Draaiboek Ransomware Aanval.docx
  ├── Geheimhoudingsverklaringen.docx
  ├── Procedure datalekken.docx
  └── Reglement IT-apparatuur en elektronische communicatiemiddelen.docx
```
