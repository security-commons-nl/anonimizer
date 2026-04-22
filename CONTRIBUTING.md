# Bijdragen aan anonimizer

Iets delen of verbeteren? Drie manieren, van makkelijk naar technisch.

## 1. Iets aanbieden of melden — geen Git-ervaring nodig

→ [**Bijdrage aanbieden**](https://github.com/security-commons-nl/anonimizer/issues/new?template=bijdrage-aanbieden.md)
  Een document, idee of aanpak die je wilt delen.

→ [**Fout of verbetering**](https://github.com/security-commons-nl/anonimizer/issues/new?template=fout-of-verbetering.md)
  Iets klopt niet, kan beter, of mist.

Vul alleen de vragen in die voor jou relevant zijn — we helpen je met de rest.

**Geen GitHub-account?** [Maak er gratis een](https://github.com/signup) (2 minuten), of vraag iemand in je netwerk om namens jou te posten.

## 2. Meediscussiëren

→ [**Discussions**](../../discussions)

Voor vragen, ervaringen en ideeën zonder directe actie.

## 3. Voor ontwikkelaars — code of testdocument aanleveren

### Meest waardevol: testdocument aanleveren

Heb je een geanonimiseerd beleidsdocument dat de detectiekwaliteit helpt meten?

1. Plaats het in `testset/`
2. Maak een `<naam>.groundtruth.json` met welke PII er in zou moeten staan (zie voorbeelden in [testset/](testset/))
3. Open een PR — CI meet automatisch of de detectie klopt

### Nieuw detectiepatroon

Wijzigingen in `patronen.py` vereisen een unit test in `tests/test_patronen.py`.

### Prompt- of flow-wijziging

Na aanpassing van `detector.py` of de pipeline: draai

```bash
python evalueer.py testset/ --no-memory
```

en voeg de P/R/F1 cijfers toe aan je PR.

### Lokale setup

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

CI draait automatisch op je PR en moet groen zijn voor merge (regex-precision = 1.0).

---

**Organisatiebrede richtlijnen**: [security-commons-nl/.github](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md)
