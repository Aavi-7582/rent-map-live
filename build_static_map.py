# build_static_map.py
# Turns the map template + file.csv + your Google Maps key into a deployable
# static page (index.html). Same 4 replacements that app.py does at runtime.
#
# Works whether this file sits at the repo root or one level down:
#     python build_static_map.py            # script next to the template
#     python scripts/build_static_map.py    # script inside scripts/
#
# Options:
#     --out map-static     output folder (default)
#     --out .              write ./index.html  (flat repo you deploy as-is)
#
# Key resolution order:
#     1) $GOOGLE_MAPS_API_KEY           (env var - use this in the new repo)
#     2) <root>/secrets.toml            (gitignore it!)
#     3) <root>/.streamlit/secrets.toml (this repo, gitignored already)
import argparse
import json
import os
import re
import sys

TEMPLATE_NAME = "map_picker_bengaluru_style.html"
CSV_NAME      = "file.csv"
HERE          = os.path.dirname(os.path.abspath(__file__))


def find_root(start):
    """Folder holding the template: `start` itself, or its parent (scripts/ layout)."""
    for candidate in (start, os.path.dirname(start)):
        if os.path.exists(os.path.join(candidate, TEMPLATE_NAME)):
            return candidate
    return None


def is_placeholder(value):
    v = (value or "").strip().upper()
    return (not v) or ("PASTE" in v) or v.startswith("YOUR_") or v in {"AIZA...", "KEY"}


def read_toml_value(path, key):
    if not os.path.exists(path):
        return ""
    try:
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s.startswith(key) and "=" in s:
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def conf(name, root):
    """env var -> <root>/secrets.toml -> <root>/.streamlit/secrets.toml."""
    for value in (os.environ.get(name, ""),
                  read_toml_value(os.path.join(root, "secrets.toml"), name),
                  read_toml_value(os.path.join(root, ".streamlit", "secrets.toml"), name)):
        if not is_placeholder(value):
            return value.strip()
    return ""


def societies_json(csv_path):
    """file.csv -> compact [{n,lat,lon}], identical to app.py:load_societies_json()."""
    try:
        import pandas as pd
    except ImportError:
        sys.exit("pandas is required to build:  pip install pandas")
    if not os.path.exists(csv_path):
        print("!! %s not found - the map will have no society pins" % CSV_NAME)
        return "[]"

    df = pd.read_csv(csv_path)
    cols = {str(c).strip().lower(): c for c in df.columns}

    def pick(*needles):
        for needle in needles:
            for k, original in cols.items():
                if needle in k:
                    return original
        return None

    name_col = pick("project_name", "society", "name")
    lat_col  = pick("latitude", "lat")
    lon_col  = pick("longitude", "lon", "lng")
    if not (name_col and lat_col and lon_col):
        print("!! could not find name/latitude/longitude columns in %s" % CSV_NAME)
        return "[]"

    out = []
    for _, row in df.iterrows():
        try:
            lat = float(str(row[lat_col]).strip())
            lon = float(str(row[lon_col]).strip())
        except (TypeError, ValueError):
            continue
        if not (15.0 < lat < 22.5 and 72.0 < lon < 81.0):   # same bounds as app.py
            continue
        name = str(row[name_col] or "").strip()
        if not name or name.lower() in ("nan", "none"):
            continue
        out.append({"n": name, "lat": round(lat, 6), "lon": round(lon, 6)})
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser(description="Build a deployable static map (index.html).")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    root = find_root(HERE)
    if not root:
        sys.exit("ERROR: %s not found in %s or %s.\n"
                 "Put this script next to the template (flat repo) or inside scripts/."
                 % (TEMPLATE_NAME, HERE, os.path.dirname(HERE)))

    template = os.path.join(root, TEMPLATE_NAME)
    out_dir  = os.path.abspath(os.path.join(root, args.out))
    os.makedirs(out_dir, exist_ok=True)

    key = conf("GOOGLE_MAPS_API_KEY", root)
    if not key:
        sys.exit("ERROR: no Google Maps key found.\n"
                 "  PowerShell : $env:GOOGLE_MAPS_API_KEY = \"AIza...\"; python build_static_map.py\n"
                 "  or file    : %s  with  GOOGLE_MAPS_API_KEY = \"AIza...\"  (gitignore it)"
                 % os.path.join(root, "secrets.toml"))

    html = open(template, encoding="utf-8").read()
    if "GOOGLE_MAPS_API_KEY_PLACEHOLDER" not in html:
        sys.exit("ERROR: %s has no placeholders left - it looks like an already-built "
                 "copy (586 KB) instead of the template (307 KB)." % template)

    html = html.replace("GOOGLE_MAPS_API_KEY_PLACEHOLDER", key)
    html = html.replace("SUPABASE_URL_PLACEHOLDER", conf("SUPABASE_URL", root))
    html = html.replace("SUPABASE_KEY_PLACEHOLDER", conf("SUPABASE_ANON_KEY", root))
    societies = societies_json(os.path.join(root, CSV_NAME))
    html = html.replace("SOCIETIES_DATA_PLACEHOLDER", societies)

    left = sorted(set(re.findall(r"[A-Z_]*PLACEHOLDER", html)))
    if left:
        sys.exit("ERROR: placeholders still present after replacement: %s" % ", ".join(left))

    index_path = os.path.join(out_dir, "index.html")
    open(index_path, "w", encoding="utf-8").write(html)
    print("wrote %s (%d bytes)" % (index_path, os.path.getsize(index_path)))
    print("society pins: %d | key: %s... | supabase: %s"
          % (societies.count('"n":'), key[:8],
             "yes" if conf("SUPABASE_URL", root) else "no (chat/listings/reviews dormant)"))

    # Backwards-compatible copy, but never overwrite the template itself.
    copy_path = os.path.join(out_dir, TEMPLATE_NAME)
    if os.path.abspath(copy_path) != os.path.abspath(template):
        open(copy_path, "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    main()

