// TopoJSON (world-atlas countries-110m) -> compact SVG path data under a plain
// equirectangular projection, plus per-country lon/lat bounding boxes for checks.
// Usage: node make_world.mjs <countries-110m.json> <out.json>
import { readFileSync, writeFileSync } from 'node:fs';

const [,, inFile, outFile] = process.argv;
const topo = JSON.parse(readFileSync(inFile, 'utf8'));
const { scale, translate } = topo.transform;

// decode arcs (delta-encoded, quantized)
const arcs = topo.arcs.map((arc) => {
  let x = 0, y = 0;
  return arc.map(([dx, dy]) => {
    x += dx; y += dy;
    return [x * scale[0] + translate[0], y * scale[1] + translate[1]];
  });
});
function ring(arcIdx) {
  const pts = [];
  for (const i of arcIdx) {
    let a = i < 0 ? arcs[~i].slice().reverse() : arcs[i];
    if (pts.length) a = a.slice(1);
    pts.push(...a);
  }
  return pts;
}

// projection: equirectangular, lon -180..180, lat clipped 84..-58 (drops Antarctica)
const W = 1000, LAT_N = 84, LAT_S = -58;
const H = Math.round(W * (LAT_N - LAT_S) / 360);
const px = (lon) => ((lon + 180) / 360) * W;
const py = (lat) => ((LAT_N - lat) / (LAT_N - LAT_S)) * H;
const r1 = (v) => Math.round(v * 10) / 10;

const out = { projection: 'equirectangular', width: W, height: H, lat_north: LAT_N, lat_south: LAT_S,
  source: 'world-atlas@2.0.2 countries-110m (Natural Earth, public domain)', countries: [] };

// A ring that crosses the antimeridian (Fiji, Russia's Chukotka) is "unwrapped": longitudes are
// made continuous (so a jump from 179 to -179 becomes 179 -> 181), and the ring is emitted twice,
// once as-is and once shifted by a full world width. The SVG viewBox clips whatever falls outside
// 0..W, so each side of the antimeridian shows exactly the part that belongs there and no fragment
// is ever closed across the map. Rings that do not cross are emitted once.
function ringPath(pts, shiftX) {
  let seg = '';
  pts.forEach(([lon, lat], i) => {
    const x = r1(px(lon) + shiftX), y = r1(py(Math.max(LAT_S, Math.min(LAT_N, lat))));
    seg += (i === 0 ? 'M' : 'L') + x + ' ' + y;
  });
  return seg + 'Z';
}
function unwrap(pts) {
  const outPts = []; let prev = null, offset = 0, crossed = false;
  for (const [lon, lat] of pts) {
    if (prev !== null) {
      if (lon - prev > 180) { offset -= 360; crossed = true; }
      else if (prev - lon > 180) { offset += 360; crossed = true; }
    }
    outPts.push([lon + offset, lat]); prev = lon;
  }
  return { pts: outPts, crossed };
}

for (const g of topo.objects.countries.geometries) {
  const name = g.properties.name;
  if (name === 'Antarctica') continue;
  const polys = g.type === 'Polygon' ? [g.arcs] : g.arcs;
  let d = '';
  let minLon = 180, maxLon = -180, minLat = 90, maxLat = -90;
  let crossesAM = false;
  for (const poly of polys) {
    for (const rIdx of poly) {
      const raw = ring(rIdx);
      for (const [lon, lat] of raw) {
        if (lon < minLon) minLon = lon; if (lon > maxLon) maxLon = lon;
        if (lat < minLat) minLat = lat; if (lat > maxLat) maxLat = lat;
      }
      const { pts, crossed } = unwrap(raw);
      if (crossed) {
        crossesAM = true;
        // decide which copies can be visible: the unwrapped ring may extend beyond either edge
        const lons = pts.map((p) => p[0]);
        const lo = Math.min(...lons), hi = Math.max(...lons);
        if (hi > -180 && lo < 180) d += ringPath(pts, 0);
        if (hi - 360 > -180 && lo - 360 < 180) d += ringPath(pts, -W);
        if (hi + 360 > -180 && lo + 360 < 180) d += ringPath(pts, W);
      } else {
        d += ringPath(pts, 0);
      }
    }
  }
  out.countries.push({ id: g.id || null, name, d,
    bbox: [r1(minLon), r1(minLat), r1(maxLon), r1(maxLat)],
    // for countries straddling the antimeridian the lon range of the bbox is meaningless
    bbox_lon_unreliable: crossesAM || undefined });
}
writeFileSync(outFile, JSON.stringify(out));
console.log(`countries=${out.countries.length} size=${(JSON.stringify(out).length / 1024).toFixed(0)}KB W=${W} H=${H} antimeridian=${out.countries.filter((c) => c.bbox_lon_unreliable).map((c) => c.name).join(',')}`);
