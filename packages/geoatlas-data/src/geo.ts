/** Point-in-polygon (ray cast). EPSG:4326 lon/lat as x/y. No invented geometry. */

function ringContains(lon: number, lat: number, ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0];
    const yi = ring[i][1];
    const xj = ring[j][0];
    const yj = ring[j][1];
    const intersect =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi + 0.0) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function polygonContains(
  lon: number,
  lat: number,
  coordinates: number[][][],
): boolean {
  const outer = coordinates[0];
  if (!outer || !ringContains(lon, lat, outer)) return false;
  for (let h = 1; h < coordinates.length; h++) {
    if (ringContains(lon, lat, coordinates[h])) return false;
  }
  return true;
}

/** True if point is inside any polygon of a FeatureCollection. */
export function pointInFeatureCollection(
  lon: number,
  lat: number,
  fc: GeoJSON.FeatureCollection | null | undefined,
): boolean {
  if (!fc?.features?.length) return false;
  for (const f of fc.features) {
    const g = f.geometry;
    if (!g) continue;
    if (g.type === "Polygon") {
      if (polygonContains(lon, lat, g.coordinates as number[][][])) return true;
    } else if (g.type === "MultiPolygon") {
      for (const poly of g.coordinates as number[][][][]) {
        if (polygonContains(lon, lat, poly)) return true;
      }
    }
  }
  return false;
}
