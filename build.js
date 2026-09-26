const fs = require("fs");
const path = require("path");

const source = path.join(__dirname, "index.html");
const outputDir = path.join(__dirname, "dist");
const output = path.join(outputDir, "index.html");

const googleKey = process.env.GOOGLE_MAPS_API_KEY;
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!googleKey) {
    throw new Error("Missing GOOGLE_MAPS_API_KEY");
}

if (!supabaseUrl) {
    throw new Error("Missing SUPABASE_URL");
}

if (!supabaseKey) {
    throw new Error("Missing SUPABASE_ANON_KEY");
}

let html = fs.readFileSync(source, "utf8");

html = html.replaceAll(
    "GOOGLE_MAPS_API_KEY_PLACEHOLDER",
    googleKey
);

html = html.replaceAll(
    "SUPABASE_URL_PLACEHOLDER",
    supabaseUrl
);

html = html.replaceAll(
    "SUPABASE_ANON_KEY_PLACEHOLDER",
    supabaseKey
);

fs.mkdirSync(outputDir, { recursive: true });

fs.writeFileSync(output, html, "utf8");

console.log("✅ Build successful");
console.log("📁 Generated: dist/index.html");