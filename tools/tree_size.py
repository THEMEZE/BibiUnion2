#!/usr/bin/env python3

## ✅ Utilisation

#Bash :
### 1) Sans limite de profondeur
#```bash
#python3 tree_size.py .
#```
### 2) Avec une profondeur maximale (ex: 2)
#```bash
#python3 tree_size.py . 2
#```
### 3) Pour un dossier spécifique avec profondeur maximale (ex: 3)
#```bash
#python3 tree_size.py /path/to/directory 3
#```
#Ou un dossier précis :
#```bash
#python3 tree_size.py /Users/guillaume/Documents
#```
#Exemple de sortie
#```scss
#├── src (12.4MB)
#│   ├── module (8.1MB)
#│   └── utils (4.2MB)
#└── README.md (2KB)
#```

#!/usr/bin/env python3
import os

# Couleurs ANSI
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

def get_size(path):
    """Retourne la taille totale d'un fichier ou dossier."""
    if os.path.isfile(path):
        return os.path.getsize(path)

    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except:
                pass
    return total


def human(size):
    """Affiche la taille en format lisible."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def color_for_size(size_bytes):
    """Choisit une couleur en fonction de la taille réelle en bytes."""

    # Seuils ajustables
    if size_bytes > 500 * 1024 * 1024:      # > 500 MB
        return RED
    elif size_bytes > 10 * 1024 * 1024:     # > 10 MB
        return GREEN
    else:
        return BLUE

def tree0(path, prefix="", depth=0, max_depth=None):
    """Affiche l'arbre des fichiers avec une profondeur maximale + taille totale."""

    if max_depth is not None and depth > max_depth:
        return

    # Taille totale du dossier courant
    total_size = get_size(path)
    total_human = human(total_size)

    print(prefix + f"📁 {os.path.basename(path)} (total: {total_human})")

    items = sorted(os.listdir(path))
    total = len(items)

    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        connector = "└── " if i == total - 1 else "├── "
        size = human(get_size(full_path))

        print(prefix + connector + f"{item} ({size})")

        if os.path.isdir(full_path):
            if max_depth is None or depth < max_depth:
                new_prefix = prefix + ("    " if i == total - 1 else "│   ")
                tree0(full_path, new_prefix, depth + 1, max_depth)



def tree(path, prefix="", depth=0, max_depth=None):
    """Affiche l'arbre trié par taille décroissante avec couleurs + taille totale."""

    if max_depth is not None and depth > max_depth:
        return

    # Taille totale du dossier courant
    total_size = get_size(path)
    total_human = human(total_size)

    print(prefix + f"📁 {os.path.basename(path)} (total: {total_human})")

    items = os.listdir(path)

    # Tri par taille décroissante
    items = sorted(items, key=lambda x: get_size(os.path.join(path, x)), reverse=True)
    total = len(items)

    for i, item in enumerate(items):
        full_path = os.path.join(path, item)
        size_bytes = get_size(full_path)
        size_human = human(size_bytes)

        connector = "└── " if i == total - 1 else "├── "

        # couleur selon taille
        col = color_for_size(size_bytes)

        print(prefix + connector + f"{col}{item} ({size_human}){RESET}")

        if os.path.isdir(full_path):
            if max_depth is None or depth < max_depth:
                new_prefix = prefix + ("    " if i == total - 1 else "│   ")
                tree(full_path, new_prefix, depth + 1, max_depth)

import subprocess
import re

def parse_bytes(s):
    """Convertit un format 1G, 200M en bytes."""
    units = {"B":1, "K":1024, "M":1024**2, "G":1024**3, "T":1024**4}
    match = re.match(r"([\d\.]+)([BKMGTP])", s)
    if not match:
        return 0
    value, unit = match.groups()
    return float(value) * units[unit]

def get_apfs_stats():
    """Retourne les infos APFS internes via diskutil."""
    out = subprocess.check_output(["diskutil", "apfs", "list"]).decode()

    # Taille purgeable APFS
    purgeable = 0
    m = re.search(r"Purgeable\s*:\s*([0-9\.]+ [TGMBK])", out)
    if m:
        purgeable = parse_bytes(m.group(1).replace(" ", ""))

    return purgeable

def get_snapshots():
    """Liste les snapshots et calcule la taille totale."""
    out = subprocess.check_output(["tmutil", "listlocalsnapshots", "/"]).decode()
    snaps = re.findall(r"com\.apple\.TimeMachine\.(.+)", out)

    total_size = 0
    for snap in snaps:
        try:
            info = subprocess.check_output(
                ["tmutil", "calculatesize", f"/.MobileBackups/LocalSnapshots/{snap}"]
            ).decode()
            m = re.search(r"(\d+)\s+bytes", info)
            if m:
                total_size += int(m.group(1))
        except:
            pass

    return snaps, total_size

def get_disk_usage():
    """Retourne ce que macOS affiche (Finder) et ce que disque APFS contient réellement."""
    # Finder data (df)
    out = subprocess.check_output(["df", "-H", "/"]).decode()
    lines = out.split("\n")[1].split()
    finder_used = parse_bytes(lines[2] + "B")  # DF n’affiche pas l’unité
    finder_size = parse_bytes(lines[1] + "B")

    # Real APFS usage (Python)
    st = os.statvfs("/")
    real_used = (st.f_blocks - st.f_bfree) * st.f_frsize

    return finder_used, real_used, finder_size

def tree1():
    """Analyse complète APFS : purgeable, snapshots, Finder vs réel."""
    print("\n==================== APFS ANALYSE ====================\n")

    # Purgeable
    purgeable = get_apfs_stats()
    print(f"🟦 Espace purgeable APFS      : {human(purgeable)}")

    # Snapshots
    snaps, snap_size = get_snapshots()
    print(f"🟧 Snapshots Time Machine     : {len(snaps)} snapshot(s), {human(snap_size)}")
    if len(snaps) > 0:
        for s in snaps:
            print("   ├── " + s)

    # Disk usage
    finder_used, real_used, total = get_disk_usage()
    print(f"\n🟩 Utilisé selon Finder       : {human(finder_used)}")
    print(f"🟥 Utilisé APFS réel          : {human(real_used)}")
    print(f"🟪 Capacité totale            : {human(total)}")

    # Différence
    diff = real_used - finder_used
    print(f"\n⚠️  Différence réelle - Finder : {human(diff)}")

    print("\n======================================================\n")


if __name__ == "__main__":
    import sys

    base = sys.argv[1] if len(sys.argv) > 1 else "."
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"\n📁 Arborescence triée par taille pour : {base}")
    if max_depth is not None:
        print(f"🔎 Profondeur maximale : {max_depth}")
    print()

    #tree0(base, max_depth=max_depth)

    # Séparateur entre les deux affichages
    print("\n" + "="*40 + "\n")
    print(f"📁 Arborescence colorée triée par taille pour : {
base}")
    if max_depth is not None:
        print(f"🔎 Profondeur maximale : {max_depth}"      )
    print()

    tree(base, max_depth=max_depth)
    
    print("\n" + "="*40 + "\n")
    tree1()
