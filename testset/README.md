# Testset — anonimizer

Set om detectie-kwaliteit te meten. In de repo staat alleen de synthetische set (`synth-edge-cases.md`);
groundtruth-bestanden voor echte beleidsdocumenten houd je lokaal (zie `.gitignore`), omdat ze de
gevonden persoonsgegevens letterlijk bevatten.

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

De testdocumenten en hun groundtruth-bestanden staan niet in git: het zijn interne beleidsstukken van een
organisatie, en de groundtruth bevat letterlijk de persoonsgegevens die erin gevonden zijn. Zet je eigen
documenten in `testset/` en maak per document een `<naam>.groundtruth.json` (formaat: zie
`synth-edge-cases.md.groundtruth.json`). Alleen de synthetische set is publiek.
