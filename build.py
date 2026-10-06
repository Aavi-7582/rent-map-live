import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

html_source = BASE_DIR / "index.html"
js_source = BASE_DIR / "app.js"
css_source = BASE_DIR / "style.css"

DIST_DIR = BASE_DIR / "dist"

google_key = os.environ.get("GOOGLE_MAPS_API_KEY")
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

if not google_key:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")

if not supabase_url:
    raise RuntimeError("Missing SUPABASE_URL")

if not supabase_key:
    raise RuntimeError("Missing SUPABASE_ANON_KEY")

DIST_DIR.mkdir(parents=True, exist_ok=True)

html = html_source.read_text(encoding="utf-8")

(DIST_DIR / "index.html").write_text(
    html,
    encoding="utf-8"
)

js = js_source.read_text(encoding="utf-8")

js = js.replace(
    "GOOGLE_MAPS_API_KEY_PLACEHOLDER",
    google_key
)

js = js.replace(
    "SUPABASE_URL_PLACEHOLDER",
    supabase_url
)

js = js.replace(
    "SUPABASE_ANON_KEY_PLACEHOLDER",
    supabase_key
)

(DIST_DIR / "app.js").write_text(
    js,
    encoding="utf-8"
)

shutil.copy2(
    css_source,
    DIST_DIR / "style.css"
)

print("✅ Build successful")
print("📁 Generated: dist/index.html")
print("📁 Generated: dist/style.css")
print("📁 Generated: dist/app.js")