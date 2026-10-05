import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

source = BASE_DIR / "index.html"
output = BASE_DIR / "dist" / "index.html"

google_key = os.environ.get("GOOGLE_MAPS_API_KEY")
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

if not google_key:
    raise RuntimeError("Missing GOOGLE_MAPS_API_KEY")

if not supabase_url:
    raise RuntimeError("Missing SUPABASE_URL")

if not supabase_key:
    raise RuntimeError("Missing SUPABASE_ANON_KEY")

html = source.read_text(encoding="utf-8")

html = html.replace("GOOGLE_MAPS_API_KEY_PLACEHOLDER", google_key)
html = html.replace("SUPABASE_URL_PLACEHOLDER", supabase_url)
html = html.replace("SUPABASE_ANON_KEY_PLACEHOLDER", supabase_key)

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(html, encoding="utf-8")

print("✅ Build successful")
print("📁 Generated: dist/index.html")