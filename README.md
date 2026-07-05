# Mes Copies — Éco-Droit STMG

PWA de restitution des copies corrigées pour la **Première STMG** et la **Terminale STMG** en Économie-Droit. Chaque élève se connecte avec un code personnel anonyme et retrouve : ses copies avec le retour détaillé question par question, sa progression dans le programme, sa position (anonyme) par rapport à la classe et ses badges.

**Tester tout de suite** : codes de démo `demo1` (Première) et `demot` (Terminale). Supprime les deux fichiers `data/eleves/demo*.json` et les devoirs `*-demo-*` de `devoirs.json` avant la mise en production.

---

## 1. Mise en ligne (une seule fois)

1. Crée un repo GitHub **public** (ex. `mes-copies`) et pousse tout le contenu de ce dossier.
2. Sur GitHub : *Settings → Pages → Source : Deploy from a branch → main → / (root)*.
3. L'app est en ligne sur `https://<ton-user>.github.io/mes-copies/`.
4. Sur téléphone, les élèves ouvrent l'URL puis **« Ajouter à l'écran d'accueil »** : l'app s'installe comme une application native (icône, plein écran, hors-ligne).

## 2. Générer les codes élèves (une fois par classe)

1. Prépare un CSV `liste_eleves.csv` avec les colonnes `nom,prenom`.
2. Ouvre `scripts/generate_codes.py` et **personnalise la variable `SEL`** (phrase secrète, à ne plus jamais changer).
3. Lance :
   ```bash
   python scripts/generate_codes.py liste_eleves.csv 1STMG
   python scripts/generate_codes.py liste_eleves.csv TSTMG
   ```
4. Tu obtiens `codes_prives_1STMG.csv` / `codes_prives_TSTMG.csv` : la correspondance nom ↔ code. **Ces fichiers restent sur ton ordinateur** (le `.gitignore` les bloque). Distribue à chaque élève son code sur papier individuel ou par message privé Pronote.

## 3. Publier un devoir corrigé (le workflow régulier)

1. Ton pipeline Claude Code corrige les copies comme d'habitude (barème JSON, checklists).
2. En fin de correction, demande à Claude Code de produire un fichier `resultats_devoir.json` au format de `scripts/exemple_resultats.json` : les `retours` par question sont directement dérivés de la checklist du barème (tutoiement, pas d'appréciation générale).
3. Intègre puis publie :
   ```bash
   python scripts/update_app_data.py resultats_devoir.json --codes codes_prives_TSTMG.csv
   git add data/ && git commit -m "Devoir n°3 TSTMG" && git push
   ```
   Le script ajoute le devoir à `devoirs.json`, calcule moyenne et percentiles, et met à jour chaque `data/eleves/<code>.json`. Deux minutes après le push, les élèves voient leur copie.
4. *(Optionnel)* Dépose les PDF annotés dans un dossier `pdfs/` du repo et renseigne le champ `pdf` de chaque élève dans les résultats.

## 4. RGPD — règles intégrées au projet

- **Aucun nom dans le repo public** : uniquement des codes à 6 caractères non devinables (hachage salé). Le prénom affiché dans l'app est saisi par l'élève et reste dans le `localStorage` de son téléphone.
- **Pas de classement nominatif** : l'app affiche la moyenne de classe et « X % d'élèves derrière toi », jamais un rang ni les notes des autres.
- Les fichiers de correspondance sont exclus de Git par le `.gitignore`.
- Recommandé : informer les familles (mot carnet/Pronote) et déclarer le traitement au DPO académique.

## 5. Personnalisation

- **Thèmes du programme** : modifiables dans `data/devoirs.json` (`programme`), les identifiants `d1..d8` / `e1..e9` servent de référence dans les devoirs.
- **Couleurs** : accent par classe dans `devoirs.json` (`classes.*.accent`).
- **Badges** : la liste et les règles sont dans `app/index.html` (tableau `BADGES`), tout est calculé côté élève.
- Après modification de `index.html`/`app/index.html`, incrémente `VERSION` dans `sw.js` pour forcer la mise à jour chez les élèves.

## Structure

```
index.html            Écran de connexion par code
app/index.html        Application (copies, progression, badges)
manifest.json, sw.js  Installation PWA + hors-ligne
icons/                Icônes de l'app
data/devoirs.json     Classes, programmes, liste des devoirs
data/eleves/*.json    Un fichier par élève (anonyme)
scripts/              generate_codes.py, update_app_data.py, exemple_resultats.json
```
