#!/usr/bin/env python3
"""
Génère les codes personnels anonymes des élèves.

Usage :
    python generate_codes.py liste_eleves.csv 1STMG
    python generate_codes.py liste_eleves.csv TSTMG

Entrée : un CSV avec les colonnes  nom,prenom  (une ligne par élève).

Sorties :
    1. codes_prives_<CLASSE>.csv  → la correspondance nom/prénom ↔ code.
       ⚠️ FICHIER PRIVÉ : à garder sur ton ordinateur, JAMAIS dans le repo
       (il est couvert par le .gitignore fourni).
    2. ../data/eleves/<code>.json → un squelette vide par élève,
       que l'app peut déjà charger (écran « aucune copie »).

Le code est dérivé d'un hachage nom+prénom+SEL : stable dans le temps
(relancer le script redonne les mêmes codes) et impossible à deviner
sans connaître le sel.
"""

import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

# ── À PERSONNALISER UNE FOIS POUR TOUTES ────────────────────────────────
# Change ce sel par une phrase de ton choix, puis n'y touche plus jamais
# (sinon tous les codes changent). Ne le publie nulle part.
SEL = "CHANGE-MOI-phrase-secrete-du-prof"
# ────────────────────────────────────────────────────────────────────────

ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # sans 0/O, 1/l/i : lisible au tableau


def make_code(nom: str, prenom: str, classe: str) -> str:
    h = hashlib.sha256(f"{nom.strip().lower()}|{prenom.strip().lower()}|{classe}|{SEL}".encode()).digest()
    n = int.from_bytes(h[:8], "big")
    code = ""
    for _ in range(6):
        code += ALPHABET[n % len(ALPHABET)]
        n //= len(ALPHABET)
    return code


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage : python generate_codes.py liste_eleves.csv <1STMG|TSTMG>")

    csv_path = Path(sys.argv[1])
    classe = sys.argv[2].upper()
    if classe not in ("1STMG", "TSTMG"):
        sys.exit("La classe doit être 1STMG ou TSTMG.")
    if SEL == "CHANGE-MOI-phrase-secrete-du-prof":
        sys.exit("⚠️  Personnalise d'abord la variable SEL dans ce script.")

    eleves_dir = Path(__file__).resolve().parent.parent / "data" / "eleves"
    eleves_dir.mkdir(parents=True, exist_ok=True)

    lignes = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            nom, prenom = row["nom"].strip(), row["prenom"].strip()
            code = make_code(nom, prenom, classe)
            lignes.append((nom, prenom, code))

            fichier = eleves_dir / f"{code}.json"
            if not fichier.exists():
                fichier.write_text(
                    json.dumps(
                        {"code": code, "classe": classe, "maj": date.today().isoformat(), "copies": []},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

    doublons = len(lignes) - len({c for *_, c in lignes})
    if doublons:
        sys.exit("⚠️  Collision de codes détectée (très rare) : change légèrement le SEL et relance.")

    sortie = Path(f"codes_prives_{classe}.csv")
    with open(sortie, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nom", "prenom", "code"])
        w.writerows(sorted(lignes))

    print(f"✅ {len(lignes)} codes générés pour la {classe}.")
    print(f"   → Correspondance privée : {sortie}  (NE PAS COMMIT)")
    print(f"   → Squelettes créés dans : {eleves_dir}")
    print("   Distribue à chaque élève son code (petit papier individuel ou Pronote en MP).")


if __name__ == "__main__":
    main()
