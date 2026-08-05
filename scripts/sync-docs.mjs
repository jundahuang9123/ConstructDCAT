import { createHash } from "node:crypto";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const docs = path.join(root, "docs");
const release = path.join(docs, "releases", "0.1.0");
const latest = path.join(docs, "releases", "latest");
const releaseSnapshot = path.join(release, "index.html");
const vendorCssPath = path.join(root, "spec", "vendor", "w3c-base.css");

await mkdir(release, { recursive: true });
await mkdir(latest, { recursive: true });
await mkdir(path.join(release, "examples"), { recursive: true });
await mkdir(path.join(release, "queries"), { recursive: true });
await mkdir(path.join(latest, "examples"), { recursive: true });
await mkdir(path.join(latest, "queries"), { recursive: true });

const renderedSnapshot = await readFile(releaseSnapshot, "utf8");
const sourceBytes = await readFile(path.join(root, "spec", "index.html"));
const vendorCssBytes = await readFile(vendorCssPath);
const vendorCss = vendorCssBytes
  .toString("utf8")
  .replace(
    /url\(https:\/\/www\.w3\.org\/StyleSheets\/TR\/2021\/logos\/UD-watermark[^)]+\)/g,
    "none",
  );
const buildHash = createHash("sha256")
  .update(sourceBytes)
  .update("\0")
  .update(vendorCssBytes)
  .digest("hex");
const snapshot = renderedSnapshot
  .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
  .replace(
    /(?:<link rel="stylesheet" href="https:\/\/www\.w3\.org\/StyleSheets\/TR\/2021\/base\.css">|<style id="construct-dcat-vendored-base">[\s\S]*?<\/style>)/i,
    `<style id="construct-dcat-vendored-base">\n${vendorCss}\n</style>`,
  )
  .replace(
    /\s*<meta name="construct-dcat-(?:source|build)-sha256" content="[a-f0-9]{64}">/i,
    "",
  )
  .replace(/[ \t]+$/gm, "")
  .replace(
    "</head>",
    `  <meta name="construct-dcat-build-sha256" content="${buildHash}">\n</head>`,
  );
const forbiddenRuntimeMarkers = [
  "<script",
  "respecConfig",
  "respec-w3c",
  "www.w3.org/Tools/respec",
];

for (const marker of forbiddenRuntimeMarkers) {
  if (snapshot.includes(marker)) {
    throw new Error(`Static snapshot still contains a ReSpec runtime marker: ${marker}`);
  }
}

await writeFile(releaseSnapshot, snapshot, "utf8");

await Promise.all([
  copyFile(releaseSnapshot, path.join(docs, "index.html")),
  copyFile(releaseSnapshot, path.join(latest, "index.html")),
  copyFile(path.join(root, "construct-dcat.ttl"), path.join(docs, "construct-dcat.ttl")),
  copyFile(path.join(root, "construct-dcat.jsonld"), path.join(docs, "construct-dcat.jsonld")),
  copyFile(path.join(root, "construct-dcat.ttl"), path.join(release, "construct-dcat.ttl")),
  copyFile(path.join(root, "construct-dcat.jsonld"), path.join(release, "construct-dcat.jsonld")),
  copyFile(path.join(root, "construct-dcat.ttl"), path.join(latest, "construct-dcat.ttl")),
  copyFile(path.join(root, "construct-dcat.jsonld"), path.join(latest, "construct-dcat.jsonld")),
  copyFile(path.join(root, "examples", "example-catalog.ttl"), path.join(release, "examples", "example-catalog.ttl")),
  copyFile(path.join(root, "examples", "example-catalog.ttl"), path.join(latest, "examples", "example-catalog.ttl")),
  copyFile(path.join(root, "queries", "wall-bot.rq"), path.join(release, "queries", "wall-bot.rq")),
  copyFile(path.join(root, "queries", "wall-bot.rq"), path.join(latest, "queries", "wall-bot.rq")),
  copyFile(path.join(root, "CITATION.cff"), path.join(release, "CITATION.cff")),
  copyFile(path.join(root, "CITATION.cff"), path.join(latest, "CITATION.cff")),
]);

console.log("Synchronized the static specification and RDF serializations.");
