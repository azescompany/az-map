/**
 * Offline smoke for places cascade (mirrors loadPlacesForArea rules).
 * Usage: node scripts/smoke_places_cascade.mjs
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const areas = JSON.parse(
  fs.readFileSync(path.join(root, "data/areas/areas.json"), "utf8"),
).areas;

function getArea(id) {
  return areas.find((a) => a.id === id);
}
function verifiedChildren(parentId) {
  return areas.filter(
    (a) => a.parent_id === parentId && a.parent_status === "verified",
  );
}
function areaKey(boundaryFile) {
  if (!boundaryFile) return null;
  const p = boundaryFile.replace(/\\/g, "/");
  return (
    /rayon_([a-z0-9_]+)\.geojson$/i.exec(p)?.[1] ??
    /city_([a-z0-9_]+)\.geojson$/i.exec(p)?.[1] ??
    null
  );
}
function resolveFile(area) {
  if (area.type === "rayon" || area.type === "city") {
    const key = areaKey(area.boundary_file);
    if (key) return `places/${key}_all.json`;
    return null;
  }
  if (area.type === "neighborhood" || area.type === "settlement") {
    if (area.name === "Masazır" || area.boundary_file?.includes("masazir")) {
      return "places/masazir_all.json";
    }
    if (area.name === "Xırdalan" || area.boundary_file?.includes("xirdalan")) {
      return "places/xirdalan_all.json";
    }
    const parent = area.parent_id ? getArea(area.parent_id) : undefined;
    if (parent) return resolveFile(parent);
  }
  return null;
}
function readPlaces(file) {
  const full = path.join(root, "data", file);
  if (!fs.existsSync(full)) return [];
  return JSON.parse(fs.readFileSync(full, "utf8")).places ?? [];
}
function named(places) {
  return places.filter(
    (p) => typeof p.name === "string" && p.name.trim().length > 0,
  );
}
function loadFor(area) {
  if (area.type === "country") return [];
  const kids = verifiedChildren(area.id);
  const rayonKids = kids.filter((k) => k.type === "rayon");
  const parent = area.parent_id ? getArea(area.parent_id) : undefined;
  const ownFile = resolveFile(area);
  const absheronCascade =
    area.type === "rayon" &&
    parent?.type === "country" &&
    kids.some((c) => {
      if (c.type !== "neighborhood" && c.type !== "settlement") return false;
      const cf = resolveFile(c);
      return cf && cf !== ownFile;
    });

  if ((area.type === "city" && rayonKids.length) || absheronCascade) {
    const byId = new Map();
    if (ownFile) for (const p of readPlaces(ownFile)) byId.set(p.id, p);
    for (const child of kids) {
      if (child.type === "rayon") {
        const f = resolveFile(child);
        if (f) for (const p of readPlaces(f)) byId.set(p.id, p);
        continue;
      }
      if (child.type !== "neighborhood" && child.type !== "settlement") continue;
      const cf = resolveFile(child);
      if (!cf || cf === ownFile) continue;
      for (const p of readPlaces(cf)) byId.set(p.id, p);
    }
    return [...byId.values()];
  }

  if (!ownFile) return [];
  const places = readPlaces(ownFile);
  if (area.type === "rayon" || area.type === "city") return places;
  const byArea = places.filter((p) => p.area_id === area.id);
  if (byArea.length) return byArea;
  const bb = area.bbox;
  if (!bb || bb.length < 4) return [];
  return places.filter(
    (p) =>
      p.coordinates &&
      p.coordinates.lon >= bb[0] &&
      p.coordinates.lon <= bb[2] &&
      p.coordinates.lat >= bb[1] &&
      p.coordinates.lat <= bb[3],
  );
}

const baki = areas.find((a) => a.name === "Bakı" && a.type === "city");
const yasamal = areas.find((a) => a.name === "Yasamal rayonu");
const alatava = areas.find((a) => a.name === "2-ci Alatava");
const sum = areas.find((a) => a.name === "Sumqayıt" && a.type === "city");

const rows = [
  ["Bakı", baki],
  ["Yasamal", yasamal],
  ["2-ci Alatava", alatava],
  ["Sumqayıt", sum],
];
for (const [label, area] of rows) {
  const all = loadFor(area);
  const n = named(all).length;
  console.log(`${label}: raw=${all.length} named=${n}`);
}
