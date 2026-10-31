# Build sea/land polygons from OSM coastlines for the map bbox.
# Output: OSM XML with one natural=sea rectangle and natural=nosea land polygons
# (mapsforge convention: draw sea first, then land on top).
import osmium
from shapely.geometry import LineString, Polygon, box, Point
from shapely.ops import polygonize, unary_union, linemerge
from shapely.strtree import STRtree
from xml.sax.saxutils import escape

BBOX = (119.45, 35.40, 121.62, 37.20)
SRC = 'data/qingdao.osm.pbf'
OUT = 'data/sea.osm'


def build():
    """Return (frame polygon, list of land polygons) for the bbox."""
    lines = []
    for o in osmium.FileProcessor(SRC).with_locations():
        if o.is_way() and o.tags.get('natural') == 'coastline':
            pts = [(n.lon, n.lat) for n in o.nodes if n.location.valid()]
            if len(pts) >= 2:
                lines.append(LineString(pts))
    print('coastline ways', len(lines))
    frame = box(*BBOX)
    coast = unary_union([l.intersection(frame) for l in lines])
    noded = unary_union([coast, frame.exterior])
    faces = list(polygonize(noded))
    print('faces', len(faces))

    # Coastline convention: land on the left, sea on the right of the way direction.
    tree = STRtree(faces)
    votes = [0] * len(faces)
    eps = 1e-5
    for l in lines:
        c = list(l.coords)
        for i in range(0, len(c) - 1, max(1, (len(c) - 1) // 20 or 1)):
            (x1, y1), (x2, y2) = c[i], c[i + 1]
            dx, dy = x2 - x1, y2 - y1
            n = (dx * dx + dy * dy) ** 0.5
            if n == 0:
                continue
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            left = Point(mx - dy / n * eps, my + dx / n * eps)
            right = Point(mx + dy / n * eps, my - dx / n * eps)
            for p, v in ((left, 1), (right, -1)):
                for idx in tree.query(p):
                    if faces[idx].contains(p):
                        votes[idx] += v
    land = [f for f, v in zip(faces, votes) if v > 0]
    sea = [f for f, v in zip(faces, votes) if v < 0]
    unknown = [f for f, v in zip(faces, votes) if v == 0]
    print('land', len(land), 'sea', len(sea), 'unknown', len(unknown))
    land_geom = unary_union(land + unknown)  # faces without coast are inland -> land
    polys = list(land_geom.geoms) if hasattr(land_geom, 'geoms') else [land_geom]
    return frame, [p for p in polys if p.area > 1e-9]


def main():
    frame, polys = build()
    nid, wid, rid = [-1], [-1], [-1]
    nodes, ways, rels = [], [], []

    def ring(coords, tags=None):
        refs = []
        coords = list(coords)
        first = None
        for x, y in coords[:-1]:
            nodes.append(f'<node id="{nid[0]}" version="1" lat="{y:.7f}" lon="{x:.7f}"/>')
            refs.append(nid[0])
            nid[0] -= 1
        refs.append(refs[0])
        w = wid[0]
        wid[0] -= 1
        t = ''.join(f'<tag k="{k}" v="{escape(v)}"/>' for k, v in (tags or {}).items())
        ways.append(f'<way id="{w}" version="1">' + ''.join(f'<nd ref="{r}"/>' for r in refs) + t + '</way>')
        return w

    ring(frame.exterior.coords, {'natural': 'sea', 'layer': '-5'})
    for p in polys:
        p = p.simplify(0.00001)
        if p.is_empty or p.area < 1e-9:
            continue
        if len(p.interiors) == 0:
            ring(p.exterior.coords, {'natural': 'nosea', 'layer': '-5'})
        else:
            outer = ring(p.exterior.coords)
            inners = [ring(i.coords) for i in p.interiors]
            m = ''.join(f'<member type="way" ref="{outer}" role="outer"/>')
            m += ''.join(f'<member type="way" ref="{i}" role="inner"/>' for i in inners)
            rels.append(f'<relation id="{rid[0]}" version="1">{m}<tag k="type" v="multipolygon"/>'
                        f'<tag k="natural" v="nosea"/><tag k="layer" v="-5"/></relation>')
            rid[0] -= 1
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="build_sea">\n')
        # osmosis expects descending order for negative ids within each type
        f.write('\n'.join(nodes) + '\n' + '\n'.join(ways) + '\n' + '\n'.join(rels) + '\n</osm>\n')
    print('nodes', len(nodes), 'ways', len(ways), 'rels', len(rels))


if __name__ == '__main__':
    main()
