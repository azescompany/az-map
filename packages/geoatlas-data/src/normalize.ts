export function normalize(s: string): string {
  let out = (s || "").toLocaleLowerCase("az");
  out = out
    .replace(/ə/g, "e")
    .replace(/ı/g, "i")
    .replace(/ö/g, "o")
    .replace(/ü/g, "u")
    .replace(/ğ/g, "g")
    .replace(/ş/g, "s")
    .replace(/ç/g, "c");
  return out.replace(/[^a-z0-9]+/g, " ").trim().replace(/\s+/g, " ");
}
