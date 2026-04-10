"""Load always-apply replacements from standaard.yaml."""
import pathlib
import yaml

STANDAARD_PAD = pathlib.Path(__file__).parent / "standaard.yaml"


def laad() -> dict[str, str]:
    """Return {original: replacement} dict. Empty dict if file does not exist."""
    if not STANDAARD_PAD.exists():
        return {}
    try:
        data = yaml.safe_load(STANDAARD_PAD.read_text(encoding="utf-8")) or {}
        return data.get("vervangingen", {})
    except (yaml.YAMLError, OSError):
        return {}
