# Bijdragen aan anonimizer

Bedankt voor je interesse. Deze repo volgt de organisatiebrede richtlijnen van security-commons-nl:

- [CONTRIBUTING.md (org-wide)](https://github.com/security-commons-nl/.github/blob/main/CONTRIBUTING.md)
- [DOCUMENTATION-STANDARD.md](https://github.com/security-commons-nl/.github/blob/main/DOCUMENTATION-STANDARD.md)
- [PRINCIPLES.md](https://github.com/security-commons-nl/.github/blob/main/PRINCIPLES.md)

## Project-specifieke werkwijze

### Tests draaien

```bash
pip install -r requirements.txt pytest
pytest tests/ -v
```

### Detectie-kwaliteit meten

```bash
# Snelle regressie zonder API-sleutel:
python evalueer.py testset/ --offline --no-memory --min-precision 1.0

# Volledig met LLM (vereist AI_API_KEY in .env):
python evalueer.py testset/ --no-memory
```

Zie [docs/plan-aanscherping.md](docs/plan-aanscherping.md) voor het kwaliteitsframework.

### PRs

- Unit tests vereist voor nieuwe detectiepatronen (`tests/test_patronen.py`)
- Ground-truth annotaties verplicht voor nieuwe testdocumenten (`testset/<naam>.groundtruth.json`)
- CI moet groen zijn (regex-laag precision = 1.0)
