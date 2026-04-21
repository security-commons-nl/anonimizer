#!/usr/bin/env python3
"""Saneer memory.json — repareer mojibake, verwijder duplicates, normaliseer UTF-8.

Gebruik:
    python saneer_memory.py                  # toont wat er zou gebeuren (dry-run)
    python saneer_memory.py --toepassen      # past wijzigingen toe
    python saneer_memory.py --pad <pad>      # alternatief memory-bestand

Back-up wordt altijd geschreven naar memory.json.bak voordat wijzigingen
worden toegepast.

Drie typen correcties:
  1. Double-encoded UTF-8: "InitiÃ«le" → "Initiële" (bytes → cp1252 → utf-8)
  2. U+FFFD vervangen: entries met � kunnen niet hersteld worden → gemarkeerd
  3. Exacte duplicates: zelfde tekst meermaals → eerste behouden
"""
import argparse
import json
import pathlib
import shutil
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# Typische double-UTF8 patronen. Als deze in tekst zitten, is mojibake te vermoeden.
_DUBBEL_UTF8_INDICATIES = ("Ã«", "Ã©", "Ã¨", "Ã¶", "Ã¼", "Ã¯", "Ã¢", "Ãª", "â€™", "â€", "Ã ")


def _probeer_mojibake_repair(s: str) -> str | None:
    """Probeer double-UTF8-mojibake te repareren.

    Als s bytes bevat die er uitzien als CP1252-interpretatie van UTF-8,
    proberen we de originele bytes te reconstrueren.
    """
    if not any(ind in s for ind in _DUBBEL_UTF8_INDICATIES):
        return None
    try:
        # Neem de string als CP1252, decode als UTF-8
        bytes_cp1252 = s.encode("cp1252", errors="strict")
        hersteld = bytes_cp1252.decode("utf-8", errors="strict")
        # Sanity: herstelde versie moet korter zijn (dubbele encoding → enkele)
        if hersteld != s and len(hersteld) < len(s):
            return hersteld
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return None


def analyseer(entries: list[dict]) -> dict:
    """Analyseer entries en retourneer rapportage."""
    mojibake_reparabel: list[tuple[int, dict, dict]] = []
    mojibake_verloren: list[tuple[int, dict]] = []
    duplicates: list[tuple[int, dict]] = []
    goed: list[dict] = []

    gezien: dict[str, int] = {}

    for i, item in enumerate(entries):
        tekst = item.get("tekst", "")
        vervanging = item.get("vervanging", "")

        # U+FFFD: niet herstelbaar
        if "�" in tekst or "�" in vervanging:
            mojibake_verloren.append((i, item))
            continue

        # Double-UTF8 mojibake: mogelijk herstelbaar
        tekst_hersteld = _probeer_mojibake_repair(tekst)
        verv_hersteld = _probeer_mojibake_repair(vervanging)
        if tekst_hersteld is not None or verv_hersteld is not None:
            hersteld_item = dict(item)
            if tekst_hersteld is not None:
                hersteld_item["tekst"] = tekst_hersteld
            if verv_hersteld is not None:
                hersteld_item["vervanging"] = verv_hersteld
            mojibake_reparabel.append((i, item, hersteld_item))
            # Tel de herstelde key als gezien
            key = hersteld_item["tekst"]
            if key in gezien:
                duplicates.append((i, hersteld_item))
            else:
                gezien[key] = i
                goed.append(hersteld_item)
            continue

        # Duplicate check op originele tekst
        if tekst in gezien:
            duplicates.append((i, item))
            continue

        gezien[tekst] = i
        goed.append(item)

    return {
        "origineel_aantal": len(entries),
        "goed_aantal": len(goed),
        "mojibake_reparabel": mojibake_reparabel,
        "mojibake_verloren": mojibake_verloren,
        "duplicates": duplicates,
        "goed": goed,
    }


def rapporteer(analyse: dict) -> None:
    n_orig = analyse["origineel_aantal"]
    n_goed = analyse["goed_aantal"]
    n_rep = len(analyse["mojibake_reparabel"])
    n_verl = len(analyse["mojibake_verloren"])
    n_dup = len(analyse["duplicates"])

    print(f"Origineel:          {n_orig} entries")
    print(f"Reparabel mojibake: {n_rep}")
    print(f"Verloren (U+FFFD):  {n_verl}")
    print(f"Duplicates:         {n_dup}")
    print(f"Na sanering:        {n_goed} entries")
    print()

    if analyse["mojibake_reparabel"]:
        print("— Reparabel —")
        for i, oud, nieuw in analyse["mojibake_reparabel"][:10]:
            t_oud = oud.get("tekst", "")
            t_nieuw = nieuw.get("tekst", "")
            if t_oud != t_nieuw:
                print(f"  [{i:3d}] {t_oud!r} → {t_nieuw!r}")
            v_oud = oud.get("vervanging", "")
            v_nieuw = nieuw.get("vervanging", "")
            if v_oud != v_nieuw:
                print(f"  [{i:3d}] (vervanging) {v_oud!r} → {v_nieuw!r}")
        if n_rep > 10:
            print(f"  ... en nog {n_rep - 10}")
        print()

    if analyse["mojibake_verloren"]:
        print("— Verloren (handmatige review aanbevolen) —")
        for i, item in analyse["mojibake_verloren"][:10]:
            print(f"  [{i:3d}] {item.get('tekst', '')!r}")
        if n_verl > 10:
            print(f"  ... en nog {n_verl - 10}")
        print()

    if analyse["duplicates"]:
        print("— Duplicates (eerste behouden) —")
        for i, item in analyse["duplicates"][:10]:
            print(f"  [{i:3d}] {item.get('tekst', '')!r}")
        if n_dup > 10:
            print(f"  ... en nog {n_dup - 10}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--toepassen", action="store_true", help="Pas wijzigingen toe (maak eerst backup)")
    p.add_argument("--pad", type=pathlib.Path, default=pathlib.Path(__file__).parent / "memory.json")
    args = p.parse_args()

    if not args.pad.exists():
        print(f"Bestand niet gevonden: {args.pad}", file=sys.stderr)
        sys.exit(1)

    # Lees met UTF-8 assertion
    ruw = args.pad.read_text(encoding="utf-8")
    data = json.loads(ruw)
    entries = data.get("replacements", [])

    print(f"Bestand: {args.pad}\n")
    analyse = analyseer(entries)
    rapporteer(analyse)

    if not args.toepassen:
        print("\nDry-run. Gebruik --toepassen om wijzigingen door te voeren.")
        return

    # Backup
    backup_pad = args.pad.with_suffix(args.pad.suffix + ".bak")
    shutil.copy2(args.pad, backup_pad)
    print(f"\nBackup: {backup_pad}")

    # Schrijf gesaneerde versie
    schoon = {"replacements": analyse["goed"]}
    args.pad.write_text(
        json.dumps(schoon, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Geschreven: {args.pad} ({analyse['origineel_aantal']} → {analyse['goed_aantal']} entries)")

    if analyse["mojibake_verloren"]:
        print(
            f"\n⚠ {len(analyse['mojibake_verloren'])} entries met U+FFFD zijn "
            "verwijderd en niet herstelbaar. Heroverweeg of deze handmatig "
            "opnieuw moeten worden opgebouwd."
        )


if __name__ == "__main__":
    main()
