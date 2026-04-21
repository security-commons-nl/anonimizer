#!/usr/bin/env python3
"""Evalueer de anonimizer tegen een testset met ground-truth annotaties.

Gebruik:
    python evalueer.py testset/
    python evalueer.py testset/ --offline     # sla LLM-laag over (snel, gratis)
    python evalueer.py testset/ --json rapport.json

Ground truth per document:
    testset/<bestand>.groundtruth.json
    {
      "moet_gedetecteerd": [
        {"tekst": "Bas Stevens", "categorie": "persoon"},
        {"tekst": "KVK 27364192", "categorie": "nummer"}
      ],
      "moet_niet_gedetecteerd": [
        "CISO", "Naam", "Telefoonnummer"
      ]
    }

Zonder groundtruth-bestand: alleen rapport van vondsten (geen P/R/F1).
"""
import sys
import json
import pathlib
import argparse
import os

# UTF-8 op Windows-consoles zodat box-drawing karakters (─, →) niet crashen
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Zorg dat project-root op sys.path staat (we draaien vanuit een andere cwd)
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from converter import to_markdown, ONDERSTEUNDE_EXTENSIES
from patronen import detect_patronen
import memory as geheugen
import standaard as std_mod


def _laad_env() -> None:
    env_pad = pathlib.Path(__file__).parent / ".env"
    if env_pad.exists():
        for line in env_pad.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def detecteer(
    tekst: str,
    offline: bool,
    gebruik_memory: bool = True,
    gebruik_standaard: bool = True,
) -> tuple[dict[str, str], list[dict], dict[str, str]]:
    """Voer detectie uit. Retourneert (auto_mapping, llm_entiteiten, bron_per_tekst)."""
    mem = geheugen.load() if gebruik_memory else []
    std = std_mod.laad() if gebruik_standaard else {}

    auto_mapping: dict[str, str] = {}
    bron: dict[str, str] = {}

    # Laag 1: standaard
    for k, v in std.items():
        if k in tekst:
            auto_mapping[k] = v
            bron[k] = "standaard"

    # Laag 1.5: patronen
    patroon_map, _ = detect_patronen(tekst)
    for k, v in patroon_map.items():
        if k not in auto_mapping:
            auto_mapping[k] = v
            bron[k] = "patroon"

    # Laag 2: memory
    for item in mem:
        t = item.get("tekst", "")
        if t and t in tekst and t not in auto_mapping:
            auto_mapping[t] = item.get("vervanging", "")
            bron[t] = "geheugen"

    # Laag 3: LLM (alleen als niet offline)
    llm_ent: list[dict] = []
    if not offline:
        try:
            from detector import _llm_detect
            raw = _llm_detect(tekst)
            known = set(auto_mapping.keys())
            llm_ent = [{**e, "bron": "llm"} for e in raw if e.get("tekst", "") not in known]
        except Exception as e:
            print(f"  ⚠ LLM-laag overgeslagen: {e}", file=sys.stderr)

    return auto_mapping, llm_ent, bron


def _laad_groundtruth(pad: pathlib.Path) -> dict | None:
    gt_pad = pad.with_suffix(pad.suffix + ".groundtruth.json")
    if not gt_pad.exists():
        return None
    try:
        return json.loads(gt_pad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ⚠ Ground truth onleesbaar: {e}", file=sys.stderr)
        return None


import re as _re


def _norm(s: str) -> str:
    """Normaliseer whitespace voor vergelijking (DOCX kan dubbele spaties bevatten)."""
    return _re.sub(r"\s+", " ", s).strip().lower()


def _bereken_metrics(
    gedetecteerd: set[str],
    moet: set[str],
    moet_niet: set[str],
) -> dict[str, float]:
    """Precision/recall/F1 tegen ground truth.

    Vergelijking is whitespace-genormaliseerd en case-insensitive zodat
    "KVK  27364192" (dubbele spatie uit DOCX) matcht met "KVK 27364192".

    - True positive: staat in 'moet_gedetecteerd' én gedetecteerd
    - False negative: staat in 'moet' maar niet gedetecteerd
    - False positive: staat in 'moet_niet_gedetecteerd' maar wél gedetecteerd
    """
    # Normaliseer alle sets voor vergelijking
    det_norm = {_norm(s): s for s in gedetecteerd}
    moet_norm = {_norm(s): s for s in moet}
    niet_norm = {_norm(s): s for s in moet_niet}

    det_keys = set(det_norm.keys())
    moet_keys = set(moet_norm.keys())
    niet_keys = set(niet_norm.keys())

    tp = len(det_keys & moet_keys)
    fn_keys = moet_keys - det_keys
    fp_keys = det_keys & niet_keys
    fn = len(fn_keys)
    fp = len(fp_keys)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0 if tp == 0 and fp == 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp, "fn": fn, "fp": fp,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "gemiste": sorted(moet_norm[k] for k in fn_keys),
        "onterecht": sorted(det_norm[k] for k in fp_keys),
    }


def evalueer_bestand(
    pad: pathlib.Path,
    offline: bool,
    gebruik_memory: bool = True,
    gebruik_standaard: bool = True,
) -> dict:
    """Evalueer één document, retourneer rapport."""
    try:
        tekst = to_markdown(pad)
    except Exception as e:
        return {"bestand": str(pad), "fout": str(e)}

    auto_mapping, llm_ent, bron = detecteer(
        tekst, offline, gebruik_memory=gebruik_memory, gebruik_standaard=gebruik_standaard
    )

    # Alle gedetecteerde tekst-strings
    alle_detecties = set(auto_mapping.keys()) | {e["tekst"] for e in llm_ent}

    # Tellingen per bron
    per_bron = {}
    for t, b in bron.items():
        per_bron[b] = per_bron.get(b, 0) + 1
    if llm_ent:
        per_bron["llm"] = len(llm_ent)

    rapport = {
        "bestand": pad.name,
        "tekens": len(tekst),
        "totaal_detecties": len(alle_detecties),
        "per_bron": per_bron,
        "auto_mapping": [{"tekst": k, "vervanging": v, "bron": bron[k]} for k, v in sorted(auto_mapping.items())],
        "llm_entiteiten": llm_ent,
    }

    # Vergelijk met ground truth als aanwezig
    gt = _laad_groundtruth(pad)
    if gt is not None:
        moet = {e["tekst"] for e in gt.get("moet_gedetecteerd", [])}
        moet_niet = set(gt.get("moet_niet_gedetecteerd", []))
        rapport["metrics"] = _bereken_metrics(alle_detecties, moet, moet_niet)

    return rapport


def main():
    p = argparse.ArgumentParser(description="Evalueer anonimizer tegen testset.")
    p.add_argument("pad", type=pathlib.Path, help="Map met testdocumenten")
    p.add_argument("--offline", action="store_true", help="Sla LLM-laag over")
    p.add_argument("--no-memory", action="store_true", help="Sla memory.json over (toon pure regex+standaard)")
    p.add_argument("--no-standaard", action="store_true", help="Sla standaard.yaml over")
    p.add_argument("--json", type=pathlib.Path, help="Schrijf JSON-rapport naar bestand")
    args = p.parse_args()

    _laad_env()

    if not args.pad.is_dir():
        print(f"Fout: {args.pad} is geen map", file=sys.stderr)
        sys.exit(1)

    # Sluit README en andere testset-infra uit
    UITGESLOTEN_NAMEN = {"README.md", "readme.md"}
    bestanden = sorted(
        f for f in args.pad.iterdir()
        if f.suffix.lower() in ONDERSTEUNDE_EXTENSIES
        and f.name not in UITGESLOTEN_NAMEN
    )
    if not bestanden:
        print(f"Geen documenten in {args.pad}", file=sys.stderr)
        sys.exit(1)

    print(f"Evalueren van {len(bestanden)} document(en){' (offline, geen LLM)' if args.offline else ''}...\n")

    rapporten = []
    totaal_tp = totaal_fp = totaal_fn = 0

    for bestand in bestanden:
        print(f"── {bestand.name}")
        rap = evalueer_bestand(
            bestand,
            args.offline,
            gebruik_memory=not args.no_memory,
            gebruik_standaard=not args.no_standaard,
        )
        rapporten.append(rap)

        if "fout" in rap:
            print(f"   FOUT: {rap['fout']}\n")
            continue

        per_bron = rap.get("per_bron", {})
        bron_str = ", ".join(f"{b}={n}" for b, n in sorted(per_bron.items()))
        print(f"   {rap['totaal_detecties']} detecties ({bron_str})")

        if "metrics" in rap:
            m = rap["metrics"]
            totaal_tp += m["tp"]; totaal_fp += m["fp"]; totaal_fn += m["fn"]
            print(f"   P={m['precision']}  R={m['recall']}  F1={m['f1']}  (tp={m['tp']} fn={m['fn']} fp={m['fp']})")
            if m["gemiste"]:
                print(f"   gemist: {m['gemiste']}")
            if m["onterecht"]:
                print(f"   onterecht: {m['onterecht']}")
        print()

    # Totaal
    if totaal_tp + totaal_fn > 0:
        p_tot = totaal_tp / (totaal_tp + totaal_fp) if (totaal_tp + totaal_fp) > 0 else 0
        r_tot = totaal_tp / (totaal_tp + totaal_fn) if (totaal_tp + totaal_fn) > 0 else 0
        f1_tot = 2 * p_tot * r_tot / (p_tot + r_tot) if (p_tot + r_tot) > 0 else 0
        print(f"{'═' * 60}")
        print(f"TOTAAL: P={p_tot:.3f}  R={r_tot:.3f}  F1={f1_tot:.3f}  (tp={totaal_tp} fn={totaal_fn} fp={totaal_fp})")

    if args.json:
        args.json.write_text(json.dumps(rapporten, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nRapport opgeslagen: {args.json}")


if __name__ == "__main__":
    main()
