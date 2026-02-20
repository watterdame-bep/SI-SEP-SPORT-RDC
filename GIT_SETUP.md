# Configuration du dépôt Git — SI-SEP Sport RDC

Le fichier **`.gitignore`** est déjà en place. Pour lier le projet à votre dépôt GitHub, exécutez les commandes suivantes dans un terminal (PowerShell ou CMD) à la racine du projet.

## 1. Initialiser Git (si pas déjà fait)

```bash
cd "d:\WATSTORE\NGODJA\SI-SEP Sport RDC"
git init
```

## 2. Ajouter le dépôt distant

```bash
git remote add origin https://github.com/watterdame-bep/SI-SEP-SPORT-RDC.git
```

## 3. Ajouter tous les fichiers et premier commit

```bash
git add .
git status
git commit -m "Initial commit: Django backend SI-SEP Sport RDC (Gouvernance + Infrastructures)"
```

## 4. Branche principale et premier push

Si le dépôt GitHub est vide :

```bash
git branch -M main
git push -u origin main
```

Si GitHub utilise encore `master` :

```bash
git branch -M master
git push -u origin master
```

---

**Authentification GitHub :**  
Si GitHub demande un mot de passe, utilisez un **Personal Access Token** (Settings → Developer settings → Personal access tokens) à la place du mot de passe, ou configurez SSH.

Repo : [https://github.com/watterdame-bep/SI-SEP-SPORT-RDC](https://github.com/watterdame-bep/SI-SEP-SPORT-RDC)
