#!/usr/bin/env python3
"""
Intègre les résultats d'un devoir corrigé dans les données de l'app.

Usage :
    python update_app_data.py resultats_devoir.json [--codes codes_prives_1STMG.csv]

Le fichier resultats_devoir.json est produit en sortie de ton pipeline
Claude Code (voir exemple_resultats.json pour le format exact).
Les élèves peuvent y être identifiés soit par leur "code", soit par
"nom"/"prenom" si tu passes --codes (le script fait la traduction et
AUCUN nom ne finit dans les données publiées).

Ce que fait le script :
  1. Ajoute (ou met à jour) le devoir dans data/devoirs.json
  2. Calcule moyenne de classe et percentile de chaque élève
  3. Fusionne la copie de chaque élève dans data/eleves/<code>.json

Ensuite :  git add data/ && git commit -m "Devoir X" && git push
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DEVOIRS_JSON = RACINE / "data" / "devoirs.json"
ELEVES_DIR = RACINE / "data" / "eleves"


def charger(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def sauver(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def charger_mapping(csv_path: Path) -> dict:
    mapping = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cle = (row["nom"].strip().lower(), row["prenom"].strip().lower())
            mapping[cle] = row["code"].strip()
    return mapping


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("resultats", help="Fichier JSON des résultats du devoir")
    ap.add_argument("--codes", help="CSV privé nom/prenom→code (si les résultats utilisent les noms)")
    args = ap.parse_args()

    resultats = charger(Path(args.resultats))
    devoir = resultats["devoir"]
    lignes = resultats["resultats"]
    mapping = charger_mapping(Path(args.codes)) if args.codes else {}

    # 1) Upsert du devoir dans devoirs.json --------------------------------
    conf = charger(DEVOIRS_JSON)
    devoir.setdefault("note_max", 20)
    existants = [d for d in conf["devoirs"] if d["id"] == devoir["id"]]
    if existants:
        existants[0].update(devoir)
        print(f"↻ Devoir « {devoir['titre']} » mis à jour dans devoirs.json")
    else:
        conf["devoirs"].append(devoir)
        print(f"＋ Devoir « {devoir['titre']} » ajouté à devoirs.json")

    themes_valides = {t["id"] for mat in conf["programme"].get(devoir["classe"], {}).values() for t in mat}
    if devoir.get("theme") not in themes_valides:
        print(f"⚠️  Thème « {devoir.get('theme')} » inconnu pour la {devoir['classe']} — vérifie devoirs.json")

    # 2) Résolution des codes ----------------------------------------------
    for r in lignes:
        if "code" not in r:
            cle = (r["nom"].strip().lower(), r["prenom"].strip().lower())
            if cle not in mapping:
                sys.exit(f"❌ Élève introuvable dans le CSV des codes : {r['nom']} {r['prenom']}")
            r["code"] = mapping[cle]

    # 3) Statistiques de classe --------------------------------------------
    notes = sorted(float(r["note"]) for r in lignes)
    effectif = len(notes)
    moyenne = round(sum(notes) / effectif, 1)

    def percentile(note: float) -> int:
        # % d'élèves strictement en dessous (0 = dernier, jamais 100)
        return round(sum(1 for n in notes if n < note) / effectif * 100)

    # 4) Fusion dans chaque fichier élève ----------------------------------
    for r in lignes:
        fichier = ELEVES_DIR / f"{r['code']}.json"
        if fichier.exists():
            eleve = charger(fichier)
        else:
            eleve = {"code": r["code"], "classe": devoir["classe"], "copies": []}
            print(f"＋ Fichier élève créé : {r['code']}.json")

        copie = {
            "devoir_id": devoir["id"],
            "note": float(r["note"]),
            "moyenne_classe": moyenne,
            "percentile": percentile(float(r["note"])),
            "effectif": effectif,
            "pdf": r.get("pdf"),
            "retours": r.get("retours", []),
        }
        eleve["copies"] = [c for c in eleve["copies"] if c["devoir_id"] != devoir["id"]]
        eleve["copies"].append(copie)
        eleve["maj"] = date.today().isoformat()
        sauver(fichier, eleve)

    sauver(DEVOIRS_JSON, conf)
    print(f"\n✅ {effectif} copies intégrées · moyenne {moyenne}/{devoir['note_max']}")
    print("   Publie avec :  git add data/ && git commit -m \"" + devoir["titre"] + "\" && git push")


if __name__ == "__main__":
    main()
