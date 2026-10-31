# Build the offline Qingdao data set from OSM + Overture:
#   data/out/qingdao.db       search/detail SQLite database used by the app
#   data/prepared.osm.pbf     OSM data with normalized poi=* tags, fed to the mapsforge writer
# Run from the repo root (libosmium cannot open non-ASCII absolute paths on Windows).
import collections, math, os, re, sqlite3, struct, sys, time, unicodedata
import osmium
import shapely
import shapely.prepared
from shapely import wkb
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import linemerge, unary_union
from shapely.strtree import STRtree
from pypinyin import lazy_pinyin, Style
from opencc import OpenCC

sys.path.insert(0, os.path.dirname(__file__))
from categories import classify, classify_overture, PLACE, RANK, HIGHWAY

SHANDONG = 'data/shandong-latest.osm.pbf'
SRC = 'data/qingdao.osm.pbf'
OUT_PBF = 'data/prepared.osm.pbf'
OUT_DB = 'data/out/qingdao.db'
OVERTURE = 'data/overture_places.parquet'
BBOX = (119.45, 35.40, 121.62, 37.20)
CITY_REL = 3469133
T2S = OpenCC('t2s')
SYN_ID = 50_000_000_000  # synthetic OSM ids start here (far above real ids)

KIND_ADMIN, KIND_PLACE, KIND_ROAD, KIND_POI, KIND_STOP, KIND_ROUTE, KIND_ADDR, KIND_LINE = 1, 2, 3, 4, 5, 6, 7, 8
ROUTE_TYPES = {'bus': '公交', 'trolleybus': '无轨电车', 'subway': '地铁', 'light_rail': '轻轨', 'tram': '有轨电车',
               'train': '火车', 'railway': '铁路线', 'ferry': '轮渡'}
WATERWAY = {'river': '河流', 'canal': '运河/渠', 'stream': '溪流', 'drain': '排水渠', 'ditch': '沟渠'}
RAILWAY_LINE = {'rail': '铁路', 'subway': '地铁线', 'light_rail': '轻轨', 'tram': '有轨电车', 'narrow_gauge': '窄轨铁路'}
UNNAMED_OK = {'toilets', 'parking', 'fuel', 'bank', 'pharmacy', 'subway_entrance', 'post'}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def norm(s):
    if not s:
        return ''
    return T2S.convert(unicodedata.normalize('NFKC', s)).strip()


def tagdict(o):
    return {t.k: t.v for t in o.tags}


def meters(lon1, lat1, lon2, lat2):
    x = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2)) * 111320
    y = (lat2 - lat1) * 110540
    return math.hypot(x, y)


def length_m(geom):
    total = 0.0
    lines = geom.geoms if hasattr(geom, 'geoms') else [geom]
    for l in lines:
        c = list(l.coords)
        for (a, b), (x, y) in zip(c, c[1:]):
            total += meters(a, b, x, y)
    return total


def area_km2(geom):
    lat = geom.centroid.y
    return geom.area * 111.32 * 110.54 * math.cos(math.radians(lat))


# ---------------------------------------------------------------- admin areas
def load_admin():
    fab = osmium.geom.WKBFactory()

    class H(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.items = []

        def area(self, a):
            t = a.tags
            if t.get('boundary') != 'administrative' or t.get('admin_level') not in ('5', '6', '8', '10'):
                return
            try:
                g = wkb.loads(fab.create_multipolygon(a), hex=True)
            except Exception:
                return
            self.items.append({'osm': ('r' if not a.from_way() else 'w') + str(a.orig_id()),
                               'rid': a.orig_id(), 'level': int(t['admin_level']),
                               'name': norm(t.get('name', '')), 'tags': tagdict(a), 'geom': g})

    h = H()
    h.apply_file(SHANDONG, locations=True, idx='flex_mem', filters=[osmium.filter.KeyFilter('boundary')])
    city = next(i for i in h.items if i['rid'] == CITY_REL and i['level'] == 5)
    cityp = shapely.prepared.prep(city['geom'])
    admin = [i for i in h.items if i['level'] > 5 and i['name'] and cityp.contains(i['geom'].representative_point())]
    log('admin areas', collections.Counter(i['level'] for i in admin))
    return city, admin


class Locator:
    """Point -> (district, town, community) names."""

    def __init__(self, admin):
        self.levels = {}
        for lv in (6, 8, 10):
            items = [a for a in admin if a['level'] == lv]
            self.levels[lv] = (STRtree([a['geom'] for a in items]), items)

    def at(self, lon, lat):
        p = Point(lon, lat)
        out = []
        for lv in (6, 8, 10):
            tree, items = self.levels[lv]
            hit = ''
            for i in tree.query(p):
                if items[i]['geom'].contains(p):
                    hit = items[i]['name']
                    break
            out.append(hit)
        return out


# ---------------------------------------------------------------- OSM extraction
def classify_ext(t):
    rw = t.get('railway')
    if rw == 'stop':
        return None  # stop positions duplicate the station node
    if rw in ('station', 'halt') or t.get('public_transport') == 'station':
        if t.get('station') == 'subway' or t.get('subway') == 'yes':
            return 'subway', '地铁站'
        if not rw and not t.get('amenity'):
            if t.get('ferry') == 'yes':
                return 'ferry', '客运码头'
            return 'busstation', '公交场站'
    c = classify(t)
    if not c and t.get('building') and t.get('name'):
        return 'building', '建筑'
    return c


def is_stop(t):
    if t.get('railway') or t.get('subway') == 'yes' or t.get('train') == 'yes' or t.get('ferry') == 'yes':
        return False
    return t.get('highway') == 'bus_stop' or t.get('public_transport') in ('platform', 'stop_position')


def in_bbox(lon, lat):
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def load_routes():
    routes = []
    for r in osmium.FileProcessor(SRC, osmium.osm.RELATION):
        t = r.tags
        if t.get('type') != 'route' or t.get('route') not in ROUTE_TYPES and t.get('route') != 'road':
            continue
        routes.append({'id': r.id, 'tags': tagdict(r), 'members': [(m.type, m.ref, m.role) for m in r.members]})
    log('routes', len(routes))
    return routes


def extract(routes):
    route_ways = {m[1] for r in routes for m in r['members'] if m[0] == 'w'}
    route_nodes = {m[1] for r in routes for m in r['members'] if m[0] == 'n'}
    fab = osmium.geom.WKBFactory()
    D = collections.defaultdict(list)
    D['nodes'] = {}
    D['way_coords'] = {}
    for o in osmium.FileProcessor(SRC).with_areas():
        if o.is_node():
            if len(o.tags) == 0:
                continue
            t = tagdict(o)
            lon, lat = o.location.lon, o.location.lat
            if o.id in route_nodes:
                D['nodes'][o.id] = (lon, lat, t)
            if not in_bbox(lon, lat):
                continue
            point_feature(D, 'n%d' % o.id, lon, lat, t, None)
        elif o.is_way():
            if o.id in route_ways:
                D['way_coords'][o.id] = [(n.lon, n.lat) for n in o.nodes]
            if len(o.tags) == 0:
                continue
            t = tagdict(o)
            hw = t.get('highway')
            name = norm(t.get('name'))
            if hw in HIGHWAY and not name and hw in ('motorway', 'trunk') and t.get('ref'):
                name = t['ref'].split(';')[0]
            if not name or len(o.nodes) < 2:
                continue
            coords = [(n.lon, n.lat) for n in o.nodes]
            if hw in HIGHWAY:
                D['roads'].append({'id': o.id, 'name': name, 'hw': hw, 'tags': t, 'coords': coords,
                                   'nodes': [n.ref for n in o.nodes]})
            elif t.get('waterway') in WATERWAY:
                D['lines'].append({'name': name, 'type': WATERWAY[t['waterway']], 'cls': 'waterway', 'tags': t, 'coords': coords})
            elif t.get('railway') in RAILWAY_LINE:
                D['lines'].append({'name': name, 'type': RAILWAY_LINE[t['railway']], 'cls': 'railway', 'tags': t, 'coords': coords})
        elif o.is_area():
            t = tagdict(o)
            if t.get('boundary') == 'administrative' or 'highway' in t or t.get('natural') == 'coastline':
                continue
            if 'name' not in t and 'addr:housenumber' not in t:
                continue
            try:
                g = wkb.loads(fab.create_multipolygon(o), hex=True)
            except Exception:
                continue
            p = g.representative_point()
            if not in_bbox(p.x, p.y):
                continue
            osm = ('w' if o.from_way() else 'r') + str(o.orig_id())
            point_feature(D, osm, p.x, p.y, t, g)
    log('extract', {k: len(v) for k, v in D.items()})
    return D


def point_feature(D, osm, lon, lat, t, geom):
    name = norm(t.get('name'))
    f = {'osm': osm, 'lon': lon, 'lat': lat, 'tags': t, 'name': name, 'geom': geom, 'src': 'OpenStreetMap'}
    pl = t.get('place')
    if pl in PLACE and name:
        f.update(kind=KIND_PLACE, cls='place_' + pl, type=PLACE[pl][0], rank=PLACE[pl][1])
        D['places'].append(f)
        return
    if geom is None and is_stop(t):
        if name:
            D['stops'].append(f)
        return
    c = classify_ext(t)
    if c and (name or c[0] in UNNAMED_OK):
        f.update(kind=KIND_POI, cls=c[0], type=c[1], rank=RANK.get(c[0], 30))
        D['pois'].append(f)
    elif 'addr:housenumber' in t:
        f.update(kind=KIND_ADDR, cls='addr', type='门牌地址', rank=20)
        D['addrs'].append(f)


# ---------------------------------------------------------------- helpers
def cluster(geoms, dist):
    """Union-find clusters of geometries within `dist` degrees of each other."""
    parent = list(range(len(geoms)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    if len(geoms) > 1:
        tree = STRtree(geoms)
        a, b = tree.query(geoms, predicate='dwithin', distance=dist)
        for i, j in zip(a, b):
            ri, rj = find(int(i)), find(int(j))
            if ri != rj:
                parent[ri] = rj
    groups = collections.defaultdict(list)
    for i in range(len(geoms)):
        groups[find(i)].append(i)
    return list(groups.values())


def merged_lines(coord_lists):
    lines = [LineString(c) for c in coord_lists if len(c) >= 2]
    if not lines:
        return None
    m = linemerge(MultiLineString(lines))
    return m


def rep_point(g):
    if g.geom_type == 'LineString':
        return g.interpolate(0.5, normalized=True)
    from shapely.ops import nearest_points
    return nearest_points(g, g.envelope.centroid)[0]


def tag_set(segs, key):
    out = []
    for s in segs:
        for v in (s['tags'].get(key) or '').split(';'):
            v = norm(v)
            if v and v not in out:
                out.append(v)
    return out


def build_roads(D):
    feats, by_name = [], collections.defaultdict(list)
    for r in D['roads']:
        by_name[r['name']].append(r)
    for name, segs in by_name.items():
        for grp in cluster([LineString(s['coords']) for s in segs], 0.004):
            ss = [segs[i] for i in grp]
            g = merged_lines([s['coords'] for s in ss])
            ln = length_m(g)
            by_class = collections.Counter()
            for s in ss:
                by_class[s['hw']] += length_m(LineString(s['coords']))
            hw = by_class.most_common(1)[0][0]
            p = rep_point(g)
            lanes = [int(x) for x in tag_set(ss, 'lanes') if x.isdigit()]
            info = [('道路等级', HIGHWAY[hw][0])]
            for k, label in (('ref', '道路编号'), ('maxspeed', '限速'), ('surface', '路面'), ('name:en', '英文名'),
                             ('alt_name', '别名'), ('old_name', '曾用名')):
                vals = tag_set(ss, k)
                if vals:
                    if k == 'maxspeed':
                        vals = [v + ' km/h' if v.isdigit() else v for v in vals]
                    if k == 'surface':
                        vals = [SURFACE.get(v, v) for v in vals]
                    info.append((label, '、'.join(vals[:6])))
            if lanes:
                info.append(('车道数', '%d' % max(lanes) if min(lanes) == max(lanes) else '%d-%d' % (min(lanes), max(lanes))))
            if all(s['tags'].get('oneway') in ('yes', '1', '-1') for s in ss):
                bearings = []
                for s in ss:
                    (x1, y1), (x2, y2) = s['coords'][0], s['coords'][-1]
                    if s['tags'].get('oneway') == '-1':
                        x1, y1, x2, y2 = x2, y2, x1, y1
                    bearings.append(math.atan2(y2 - y1, x2 - x1))
                divided = any(abs(math.remainder(a - b, 2 * math.pi)) > 2.1 for a in bearings for b in bearings)
                info.append(('通行', '双向（上下行分离）' if divided else '单行道'))
            nb = sum(1 for s in ss if s['tags'].get('bridge') not in (None, 'no'))
            nt = sum(1 for s in ss if s['tags'].get('tunnel') not in (None, 'no'))
            if nb:
                info.append(('桥梁', '%d 段' % nb))
            if nt:
                info.append(('隧道', '%d 段' % nt))
            info.append(('全长', fmt_len(ln)))
            feats.append({'kind': KIND_ROAD, 'cls': 'road_' + hw, 'name': name, 'type': HIGHWAY[hw][0],
                          'lon': p.x, 'lat': p.y, 'geom': g.simplify(0.00003), 'bounds': g.bounds,
                          'rank': HIGHWAY[hw][1] + min(10, int(math.log10(max(ln, 10)) * 2)),
                          'info': info, 'tags': {}, 'src': 'OpenStreetMap', 'osm': 'w%d' % ss[0]['id'],
                          'segs': ss, 'alt': tag_set(ss, 'ref') + tag_set(ss, 'alt_name') + tag_set(ss, 'old_name')})
    log('roads', len(D['roads']), '->', len(feats))
    return feats


def build_lines(D):
    feats, by_name = [], collections.defaultdict(list)
    for l in D['lines']:
        by_name[(l['name'], l['cls'])].append(l)
    for (name, cls), segs in by_name.items():
        for grp in cluster([LineString(s['coords']) for s in segs], 0.01):
            ss = [segs[i] for i in grp]
            g = merged_lines([s['coords'] for s in ss])
            p = rep_point(g)
            typ = collections.Counter(s['type'] for s in ss).most_common(1)[0][0]
            info = [('类型', typ), ('长度', fmt_len(length_m(g)))]
            for k, label in (('name:en', '英文名'), ('operator', '运营'), ('usage', '用途')):
                v = tag_set(ss, k)
                if v:
                    info.append((label, '、'.join(v[:4])))
            feats.append({'kind': KIND_LINE, 'cls': cls, 'name': name, 'type': typ, 'lon': p.x, 'lat': p.y,
                          'geom': g.simplify(0.00005), 'bounds': g.bounds, 'rank': 60 if cls == 'waterway' else 58,
                          'info': info, 'tags': {}, 'src': 'OpenStreetMap', 'osm': ''})
    log('lines', len(D['lines']), '->', len(feats))
    return feats


def build_stops(D):
    feats, node_map, by_name = [], {}, collections.defaultdict(list)
    for s in D['stops']:
        by_name[s['name']].append(s)
    for name, ss in by_name.items():
        for grp in cluster([Point(s['lon'], s['lat']) for s in ss], 0.003):
            g = [ss[i] for i in grp]
            lon = sum(s['lon'] for s in g) / len(g)
            lat = sum(s['lat'] for s in g) / len(g)
            fi = len(feats)
            for s in g:
                if s['osm'][0] == 'n':
                    node_map[int(s['osm'][1:])] = fi
            feats.append({'kind': KIND_STOP, 'cls': 'busstop', 'name': name, 'type': '公交站', 'lon': lon, 'lat': lat,
                          'rank': RANK['busstop'], 'tags': g[0]['tags'], 'src': 'OpenStreetMap', 'osm': g[0]['osm'],
                          'info': [('站台/站点数', str(len(g)))], 'routes': []})
    log('stops', len(D['stops']), '->', len(feats))
    return feats, node_map


SURFACE = {'asphalt': '沥青', 'concrete': '混凝土', 'paved': '铺装', 'unpaved': '未铺装', 'gravel': '碎石',
           'paving_stones': '砖石', 'dirt': '土路', 'ground': '土路', 'sett': '石块', 'compacted': '压实土'}


def fmt_len(m):
    return '%.1f 公里' % (m / 1000) if m >= 1000 else '%d 米' % m


def strip_station(n):
    return re.sub(r'(地铁站|火车站|站)$', '', n or '')


def build_routes(D, routes, stop_map, stop_feats, pois):
    station_idx = collections.defaultdict(list)
    for i, p in enumerate(pois):
        if p['cls'] in ('subway', 'train', 'ferry'):
            station_idx[strip_station(p['name'])].append(i)
    feats = []
    for r in routes:
        t = r['tags']
        rt = t.get('route')
        coords = [D['way_coords'][m[1]] for m in r['members']
                  if m[0] == 'w' and m[1] in D['way_coords'] and not m[2].startswith('platform')]
        g = merged_lines(coords)
        if g is None:
            continue
        ref = norm(t.get('ref', ''))
        name = norm(t.get('name', ''))
        if rt == 'road':
            name = name or ref
            if not name:
                continue
        stops = []  # (name, lon, lat, target)
        if rt != 'road':
            nodes = [m for m in r['members'] if m[0] == 'n']
            pref = [m for m in nodes if m[2].startswith('stop')] or [m for m in nodes if m[2].startswith('platform')] or nodes
            for m in pref:
                nd = D['nodes'].get(m[1])
                if not nd:
                    continue
                sname = norm(nd[2].get('name', ''))
                if not sname or (stops and stops[-1][0] == sname):
                    continue
                target = None
                if m[1] in stop_map:
                    target = ('s', stop_map[m[1]])
                else:
                    best = None
                    for pi in station_idx.get(strip_station(sname), []):
                        d = meters(nd[0], nd[1], pois[pi]['lon'], pois[pi]['lat'])
                        if d < 1500 and (best is None or d < best[0]):
                            best = (d, pi)
                    if best:
                        target = ('p', best[1])
                stops.append((sname, nd[0], nd[1], target))
        if not name:
            name = (ref + ('路' if rt in ('bus', 'trolleybus') and ref and ref[-1].isdigit() else '')) or ''
        if not name:
            continue
        fr, to = norm(t.get('from', '')), norm(t.get('to', ''))
        if stops:
            fr, to = fr or stops[0][0], to or stops[-1][0]
        typ = ROUTE_TYPES.get(rt, '公路') if rt != 'road' else '国省道/公路编号'
        info = [('线路类型', typ)]
        if ref:
            info.append(('线路编号', ref))
        if fr or to:
            info.append(('起讫', '%s → %s' % (fr, to)))
        for k, label in (('operator', '运营单位'), ('network', '所属网络'), ('opening_hours', '运营时间'),
                         ('interval', '发车间隔'), ('duration', '全程时长'), ('charge', '票价'), ('fee', '收费'),
                         ('colour', '线路颜色'), ('name:en', '英文名')):
            if t.get(k):
                info.append((label, norm(t[k])))
        ln = length_m(g)
        info.append(('线路长度', fmt_len(ln)))
        if stops:
            info.append(('站点数', str(len(stops))))
        p = rep_point(g)
        fi = len(feats)
        feats.append({'kind': KIND_ROUTE, 'cls': 'route_' + rt, 'name': name, 'type': typ, 'lon': p.x, 'lat': p.y,
                      'geom': g.simplify(0.00004), 'bounds': g.bounds, 'tags': t, 'src': 'OpenStreetMap',
                      'osm': 'r%d' % r['id'], 'rank': {'subway': 88, 'train': 70, 'ferry': 65, 'road': 60}.get(rt, 62),
                      'info': info, 'stops': stops, 'ref': ref, 'alt': [ref] if ref and ref != name else []})
        for s in stops:
            if s[3]:
                tgt = stop_feats[s[3][1]] if s[3][0] == 's' else pois[s[3][1]]
                tgt.setdefault('routes', [])
                if fi not in tgt['routes']:
                    tgt['routes'].append(fi)
    log('routes built', len(feats))
    return feats


# ---------------------------------------------------------------- Overture
def overture_name(names):
    common = names.get('common') or {}
    for lang in ('zh-Hans', 'zh-CN', 'zh', 'zh-Hant'):
        if common.get(lang):
            return common[lang]
    return names.get('primary')


def load_overture(cityp):
    import duckdb
    con = duckdb.connect()
    rows = con.execute(f"""SELECT names, basic_category, taxonomy.primary, confidence, addresses, phones, websites,
                           brand, operating_status, lon, lat FROM '{OVERTURE}' WHERE confidence >= 0.5""").fetchall()
    out = []
    for names, basic, prim, conf, addrs, phones, webs, brand, status, lon, lat in rows:
        if status and status != 'open':
            continue
        names = names or {}
        name = norm(overture_name(names))
        c = classify_overture(basic, prim)
        if not name or not c or not cityp.contains(Point(lon, lat)):
            continue
        if c[0] == 'airport' and not name.endswith('机场'):
            c = ('misc', '机场设施')
        a = (addrs or [{}])[0] or {}
        bname = ((brand or {}).get('names') or {}).get('primary')
        tags = {'phone': (phones or [None])[0], 'website': (webs or [None])[0], 'addr:full': norm(a.get('freeform')),
                'addr:postcode': a.get('postcode'), 'brand': norm(bname),
                'name:en': names.get('primary') if names.get('primary') != name else None}
        out.append({'kind': KIND_POI, 'cls': c[0], 'type': c[1], 'name': name, 'lon': lon, 'lat': lat,
                    'rank': RANK.get(c[0], 30) - 3, 'src': 'Overture Maps', 'osm': '', 'geom': None,
                    'tags': {k: v for k, v in tags.items() if v}})
    log('overture usable', len(out), 'of', len(rows))
    return out


def name_key(n):
    return re.sub(r'[\s\(\)（）·\-]', '', n).lower()


def dedupe(feats, extra=None, dist=150):
    """Merge same-name features within `dist` m. With `extra`, return only the non-duplicates of extra."""
    grid = collections.defaultdict(list)
    cell = 0.002

    def key(f):
        return int(f['lon'] / cell), int(f['lat'] / cell)

    def find(f):
        k = name_key(f['name'])
        cx, cy = key(f)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for g in grid[(cx + dx, cy + dy)]:
                    gk = name_key(g['name'])
                    if (k == gk or (len(k) >= 3 and len(gk) >= 3 and (k in gk or gk in k))) and \
                            meters(f['lon'], f['lat'], g['lon'], g['lat']) < dist:
                        return g
        return None
    out = []
    for f in feats:
        g = find(f) if f['name'] else None
        if g is not None and extra is None:
            if g['geom'] is None and f['geom'] is not None:
                for k in ('osm', 'lon', 'lat', 'geom'):
                    g[k] = f[k]
            for k, v in f['tags'].items():
                g['tags'].setdefault(k, v)
            continue
        grid[key(f)].append(f)
        out.append(f)
    if extra is None:
        return out
    added = []
    for f in extra:
        g = find(f)
        if g is not None:
            for k, v in f['tags'].items():
                g['tags'].setdefault(k, v)
            continue
        grid[key(f)].append(f)
        added.append(f)
    return added


# ---------------------------------------------------------------- admin features
def admin_type(level, name):
    if level == 6:
        return '县级市' if name.endswith('市') else '市辖区'
    if level == 8:
        for suf, t in (('街道', '街道'), ('镇', '镇'), ('乡', '乡'), ('办事处', '街道办事处')):
            if name.endswith(suf):
                return t
        return '乡镇级区划'
    for suf, t in (('社区', '社区'), ('村', '行政村'), ('居委会', '居委会')):
        if name.endswith(suf):
            return t
    return '村/社区'


def build_admin(city, admin, locator, land):
    feats = []
    for a in [city] + admin:
        lv = a['level']
        g = a['geom']
        t = a['tags']
        onland = g.intersection(land)
        p = (onland if not onland.is_empty else g).representative_point()
        typ = '地级市（副省级）' if lv == 5 else admin_type(lv, a['name'])
        cls = {5: 'city', 6: 'district', 8: 'town', 10: 'community'}[lv]
        info = [('行政级别', typ)]
        if lv > 6:
            d, tw, _ = locator.at(p.x, p.y)
            parent = ' · '.join(x for x in (d, tw if lv == 10 else '') if x)
            if parent:
                info.append(('上级区划', parent))
        info.append(('面积', '约 %.1f 平方公里' % area_km2(g)))
        for k, label in (('population', '人口'), ('ref:gb', '区划代码'), ('ref', '编号'), ('name:en', '英文名'),
                         ('wikipedia', '维基百科')):
            if t.get(k):
                info.append((label, norm(t[k])))
        simp = g.simplify(0.0005 if lv <= 8 else 0.0002)
        feats.append({'kind': KIND_ADMIN, 'cls': cls, 'name': a['name'], 'type': typ, 'lon': p.x, 'lat': p.y,
                      'geom': simp, 'bounds': g.bounds, 'rank': {5: 100, 6: 98, 8: 82, 10: 58}[lv], 'level': lv,
                      'info': info, 'tags': t, 'src': 'OpenStreetMap', 'osm': a['osm'], 'full': g})
    # children links: city -> districts, district -> towns, town -> communities
    for f in feats:
        f['links'] = []
    by_level = collections.defaultdict(list)
    for f in feats:
        by_level[f['level']].append(f)
    for parent_lv, child_lv in ((5, 6), (6, 8), (8, 10)):
        for c in by_level[child_lv]:
            pt = Point(c['lon'], c['lat'])
            for p in by_level[parent_lv]:
                if p['full'].contains(pt):
                    p['links'].append(('sub', c['name'], c, c['lon'], c['lat']))
                    break
    for f in feats:
        if f['links']:
            f['links'].sort(key=lambda l: l[1])
            label = {5: '下辖区市', 6: '下辖街道/镇', 8: '下辖社区/村'}[f['level']]
            f['info'].append((label, '%d 个' % len(f['links'])))
    log('admin features', len(feats))
    return feats


# ---------------------------------------------------------------- detail text
WEEK = [('Mo', '周一'), ('Tu', '周二'), ('We', '周三'), ('Th', '周四'), ('Fr', '周五'), ('Sa', '周六'),
        ('Su', '周日'), ('PH', '节假日'), ('off', '休息'), ('closed', '休息')]
YESNO = {'yes': '是', 'no': '否', 'limited': '部分', 'designated': '专用'}
SCHOOL = {'primary': '小学', 'secondary': '中学', 'middle': '初中', 'high': '高中', 'kindergarten': '幼儿园'}


def hours_zh(s):
    for a, b in WEEK:
        s = s.replace(a, b)
    return s.replace('24/7', '全天24小时')


def poi_info(f):
    t = f['tags']
    info = [('类别', f['type'])]
    for k, label, fn in (
            ('phone', '电话', None), ('contact:phone', '电话', None), ('mobile', '手机', None),
            ('opening_hours', '营业时间', hours_zh), ('website', '网站', None), ('contact:website', '网站', None),
            ('email', '邮箱', None), ('name:en', '英文名', None), ('name:zh_pinyin', '拼音', None),
            ('alt_name', '别名', norm), ('old_name', '曾用名', norm), ('official_name', '正式名称', norm),
            ('short_name', '简称', norm), ('brand', '品牌', norm), ('operator', '运营/管理', norm),
            ('stars', '星级', lambda v: v + ' 星'), ('cuisine', '菜系', lambda v: v.replace(';', '、')),
            ('religion', '宗教', None), ('denomination', '教派', None), ('isced:level', '学段', None),
            ('school', '学校类型', lambda v: SCHOOL.get(v, v)), ('beds', '床位', None), ('rooms', '房间数', None),
            ('capacity', '容量/车位', None), ('building:levels', '楼层数', lambda v: v + ' 层'),
            ('height', '高度', lambda v: v + ' 米' if re.fullmatch(r'[\d.]+', v) else v),
            ('ele', '海拔', lambda v: v + ' 米' if re.fullmatch(r'[\d.]+', v) else v),
            ('fee', '收费', lambda v: YESNO.get(v, v)), ('charge', '价格', None),
            ('wheelchair', '无障碍', lambda v: YESNO.get(v, v)), ('internet_access', '网络', None),
            ('start_date', '建成时间', None), ('heritage', '文物保护级别', None),
            ('wikipedia', '维基百科', None), ('description', '简介', norm), ('note', '备注', norm),
            ('addr:postcode', '邮编', None), ('ref', '编号', None), ('network', '所属网络', None)):
        v = t.get(k)
        if v and not any(l == label for l, _ in info):
            info.append((label, fn(v) if fn else v))
    return info


def address_of(f):
    t = f['tags']
    if t.get('addr:full'):
        return norm(t['addr:full'])
    street, num = norm(t.get('addr:street')), norm(t.get('addr:housenumber'))
    if street:
        return street + (num + ('号' if num[-1:].isdigit() else '') if num else '')
    if num and f.get('near'):
        return f['near'] + num + ('号' if num[-1:].isdigit() else '')
    if f.get('near'):
        return f['near'] + '附近'
    return ''


# ---------------------------------------------------------------- search tokens
CJK = re.compile(r'[㐀-鿿豈-﫿]')


def tokens(s):
    """Space-separate CJK chars; keep ASCII words. Must match SearchIndex.tokenize() in the app."""
    s = unicodedata.normalize('NFKC', s or '').lower()
    out, word = [], ''
    for ch in s:
        if CJK.match(ch):
            if word:
                out.append(word)
                word = ''
            out.append(ch)
        elif ch.isascii() and ch.isalnum():
            word += ch
        else:
            if word:
                out.append(word)
                word = ''
    if word:
        out.append(word)
    return ' '.join(out)


def pinyin_tokens(name):
    full = ''.join(lazy_pinyin(name)).lower()
    ini = ''.join(lazy_pinyin(name, style=Style.FIRST_LETTER)).lower()
    full = re.sub(r'[^a-z0-9]', '', full)
    ini = re.sub(r'[^a-z0-9]', '', ini)
    return full + (' ' + ini if ini and ini != full else '')


# ---------------------------------------------------------------- geometry blob
def _varint(n, out):
    while True:
        b = n & 0x7f
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


def encode_geom(g):
    """parts, then per part: npoints + zigzag delta (1e-5 deg) pairs. Polygons store rings as parts."""
    if g is None or g.is_empty:
        return None
    parts = []

    def add(geom):
        t = geom.geom_type
        if t in ('LineString', 'LinearRing'):
            parts.append(list(geom.coords))
        elif t == 'Polygon':
            parts.append(list(geom.exterior.coords))
            for r in geom.interiors:
                parts.append(list(r.coords))
        elif hasattr(geom, 'geoms'):
            for x in geom.geoms:
                add(x)
    add(g)
    out = bytearray()
    _varint(len(parts), out)
    px = py = 0
    for p in parts:
        _varint(len(p), out)
        for x, y in p:
            ix, iy = int(round(x * 1e5)), int(round(y * 1e5))
            dx, dy = ix - px, iy - py
            _varint((dx << 1) ^ (dx >> 63), out)
            _varint((dy << 1) ^ (dy >> 63), out)
            px, py = ix, iy
    return bytes(out)


def cells_of(g, size=0.01):
    cells = set()
    lines = g.geoms if hasattr(g, 'geoms') else [g]
    for l in lines:
        c = list(l.coords)
        for (x1, y1), (x2, y2) in zip(c, c[1:]):
            n = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) / (size / 2)))
            for i in range(n + 1):
                x, y = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
                cells.add(int((y - 35) / size) * 1000 + int((x - 119) / size))
    return cells


# ---------------------------------------------------------------- assembly
def natural_key(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def assemble(D, routes, city, admin, locator, land):
    cityp = shapely.prepared.prep(city['geom'])
    pois = dedupe(D['pois'])
    places = dedupe(D['places'], dist=800)
    ov = load_overture(cityp)
    for f in ov:  # keep Overture's freeform address behind OSM street addresses
        if 'addr:full' in f['tags']:
            f['tags']['ov:addr'] = f['tags'].pop('addr:full')
    pois += dedupe(pois + places, extra=ov)
    roads = build_roads(D)
    lines = build_lines(D)
    stops, stop_map = build_stops(D)
    rfeats = build_routes(D, routes, stop_map, stops, pois)
    admins = build_admin(city, admin, locator, land)
    addrs = [a for a in D['addrs']]

    # nearest named road, used as address fallback
    rgeoms = [r['geom'] for r in roads]
    rtree = STRtree(rgeoms)

    def near_road(lon, lat):
        idx = rtree.query_nearest(Point(lon, lat), max_distance=0.003)
        return roads[int(idx[0])]['name'] if len(idx) else ''

    keep = []
    for f in admins:
        lv = f['level']
        d, tw, cm = locator.at(f['lon'], f['lat'])
        f['district'] = {5: '', 6: f['name'], 8: d, 10: d}[lv]
        f['town'] = tw if lv == 10 else ''
        f['community'] = ''
        keep.append(f)
    for f in roads + lines:
        ds, ts = [], []
        segs = f.get('segs') or []
        sample = [LineString(s['coords']).interpolate(0.5, normalized=True) for s in segs[:40]] or [Point(f['lon'], f['lat'])]
        for p in sample:
            d, tw, _ = locator.at(p.x, p.y)
            if d and d not in ds:
                ds.append(d)
            if tw and tw not in ts:
                ts.append(tw)
        if not ds:
            continue
        f['district'], f['town'], f['community'] = '、'.join(ds), '、'.join(ts[:4]), ''
        if len(ds) > 1:
            f['info'].append(('途经区市', '、'.join(ds)))
        if ts:
            f['info'].append(('途经街道/镇', '、'.join(ts[:8]) + (' 等' if len(ts) > 8 else '')))
        keep.append(f)
    for f in pois + places + stops + addrs:
        d, tw, cm = locator.at(f['lon'], f['lat'])
        if not d:
            continue
        f['district'], f['town'], f['community'] = d, tw, cm
        if f['kind'] in (KIND_POI, KIND_ADDR, KIND_STOP):
            f['near'] = near_road(f['lon'], f['lat'])
        keep.append(f)
    for f in rfeats:
        ds = []
        if f['stops']:
            pts = [(s[1], s[2]) for s in f['stops'][:: max(1, len(f['stops']) // 8)]]
        else:
            g = f['geom']
            pts = [(p.x, p.y) for p in (g.interpolate(i / 8, normalized=True) for i in range(9))] \
                if g.geom_type == 'LineString' else [(f['lon'], f['lat'])]
        for x, y in pts:
            d = locator.at(x, y)[0]
            if d and d not in ds:
                ds.append(d)
        if not ds:
            continue
        f['district'], f['town'], f['community'] = '、'.join(ds), '', ''
        if ds:
            f['info'].append(('途经区市', '、'.join(ds)))
        keep.append(f)

    # per-kind detail text + links
    for f in keep:
        f.setdefault('links', [])
        k = f['kind']
        if k in (KIND_POI, KIND_PLACE, KIND_ADDR):
            if k == KIND_PLACE:
                f['info'] = [('类型', f['type'])] + [x for x in poi_info(f)[1:]]
            elif k == KIND_ADDR:
                f['info'] = [('类型', '门牌地址')]
                if f['tags'].get('building') not in (None, 'yes'):
                    f['info'].append(('建筑类型', f['tags']['building']))
                if f['tags'].get('building:levels'):
                    f['info'].append(('楼层数', f['tags']['building:levels'] + ' 层'))
            else:
                f['info'] = poi_info(f)
            f['addr'] = address_of(f) or (norm(f['tags'].get('ov:addr')) if f['tags'].get('ov:addr') else '')
            if not f['name']:
                f['name'] = f['addr'] if k == KIND_ADDR else f['type']
                f['noname'] = True
        elif k == KIND_STOP:
            f['addr'] = (f['near'] + '附近') if f.get('near') else ''
        else:
            f['addr'] = ''
    for f in keep:
        if f['kind'] == KIND_ROUTE:
            for i, s in enumerate(f['stops']):
                tgt = None
                if s[3]:
                    tgt = stops[s[3][1]] if s[3][0] == 's' else pois[s[3][1]]
                f['links'].append(('stop', '%d. %s' % (i + 1, s[0]), tgt, s[1], s[2]))
    for coll in (stops, pois):
        for f in coll:
            if 'district' not in f:
                continue
            rs = sorted({rfeats[i]['name']: rfeats[i] for i in f.get('routes', []) if 'district' in rfeats[i]}.values(),
                        key=lambda r: natural_key(r['name']))
            if not rs:
                continue
            names = []
            for r in rs:
                dest = next((v for l, v in r['info'] if l == '起讫'), '')
                title = r['name'] if ('→' in r['name'] or '->' in r['name'] or not dest) else r['name'] + '  ' + dest
                f.setdefault('links', []).append(('route', title, r, r['lon'], r['lat']))
                if r['ref'] or r['name'] not in names:
                    names.append(r['ref'] or r['name'])
            uniq = sorted(set(names), key=natural_key)
            f['info'].append(('途经线路', '%d 条：%s' % (len(uniq), '、'.join(uniq[:40]) + (' 等' if len(uniq) > 40 else ''))))
            f['rank'] = f['rank'] + min(15, len(uniq))
    # crossing roads via shared nodes
    node_roads = collections.defaultdict(set)
    rid = {id(f): f for f in roads}
    for f in roads:
        for s in f['segs']:
            for n in s['nodes']:
                node_roads[n].add(id(f))
    for f in roads:
        seen = {}
        for s in f['segs']:
            for n in s['nodes']:
                for o in node_roads.get(n, ()):
                    if o != id(f) and o not in seen:
                        seen[o] = rid[o]
        for o in sorted(seen.values(), key=lambda r: -r['rank'])[:40]:
            f.setdefault('links', []).append(('cross', o['name'], o, o['lon'], o['lat']))
        if seen:
            f['info'].append(('相交道路', '%d 条' % len(seen)))
    # common trailing lines
    for f in keep:
        chain = ' · '.join(x for x in ('青岛市', f.get('district'), f.get('town'), f.get('community')) if x)
        if f['kind'] != KIND_ADMIN or f['level'] > 6:
            f['info'].append(('所在区域', chain))
        if f.get('addr'):
            f['info'].insert(1, ('地址', f['addr']))
        f['info'].append(('数据来源', f['src']))
        f['info'].append(('坐标', '%.6f, %.6f' % (f['lat'], f['lon'])))
    log('features', collections.Counter(f['kind'] for f in keep))
    return keep


# ---------------------------------------------------------------- database
SCHEMA = """
CREATE TABLE feature(id INTEGER PRIMARY KEY, kind INTEGER, cls TEXT, name TEXT, type TEXT, addr TEXT,
  district TEXT, info TEXT, lat REAL, lon REAL, minlat REAL, minlon REAL, maxlat REAL, maxlon REAL,
  rank INTEGER, geom BLOB, osm TEXT, level INTEGER);
CREATE VIRTUAL TABLE fts USING fts4(name, py, other, tokenize=simple);
CREATE TABLE link(fid INTEGER, seq INTEGER, rel TEXT, title TEXT, target INTEGER, lat REAL, lon REAL);
CREATE TABLE cell(cell INTEGER, fid INTEGER);
CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
"""


def write_db(feats):
    if os.path.exists(OUT_DB):
        os.remove(OUT_DB)
    db = sqlite3.connect(OUT_DB)
    db.executescript(SCHEMA)
    feats.sort(key=lambda f: (f['kind'], -f['rank']))
    for i, f in enumerate(feats):
        f['id'] = i + 1
    for f in feats:
        g = f.get('geom')
        if f['kind'] == KIND_POI and g is not None:
            g = g.simplify(0.00005) if area_km2(g) > 0.002 else None
        if f['kind'] in (KIND_ADDR, KIND_PLACE, KIND_STOP):
            g = None
        b = f.get('bounds') or (g.bounds if g is not None else None)
        info = '\n'.join('%s\t%s' % (l, v) for l, v in f['info'] if v)
        db.execute('INSERT INTO feature VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (f['id'], f['kind'], f['cls'], f['name'], f['type'], f.get('addr', ''), f.get('district', ''),
                    info, round(f['lat'], 6), round(f['lon'], 6),
                    b[1] if b else None, b[0] if b else None, b[3] if b else None, b[2] if b else None,
                    int(f['rank']), encode_geom(g), f.get('osm', ''), f.get('level')))
        alt = ' '.join(norm(x) for x in f.get('alt', []))
        t = f.get('tags') or {}
        alt += ' ' + ' '.join(norm(t.get(k, '')) for k in ('alt_name', 'old_name', 'short_name', 'official_name', 'brand', 'name:en'))
        other = ' '.join((alt, f['type'], f.get('addr', ''), f.get('district', ''), f.get('town', '')))
        db.execute('INSERT INTO fts(docid,name,py,other) VALUES(?,?,?,?)',
                   (f['id'], tokens(f['name']), pinyin_tokens(f['name']), tokens(other)))
        for seq, (rel, title, tgt, lon, lat) in enumerate(f.get('links', [])):
            db.execute('INSERT INTO link VALUES(?,?,?,?,?,?,?)',
                       (f['id'], seq, rel, title, tgt.get('id') if tgt else None, lat, lon))
        if f['kind'] in (KIND_ROAD, KIND_LINE) and f.get('geom') is not None:
            for c in cells_of(f['geom']):
                db.execute('INSERT INTO cell VALUES(?,?)', (c, f['id']))
    db.executescript("""
      CREATE INDEX feature_lat ON feature(lat);
      CREATE INDEX feature_cls ON feature(cls, lat);
      CREATE INDEX link_fid ON link(fid, seq);
      CREATE INDEX cell_cell ON cell(cell);
    """)
    db.execute("INSERT INTO meta VALUES('built', ?)", (time.strftime('%Y-%m-%d'),))
    db.execute("INSERT INTO meta VALUES('count', ?)", (str(len(feats)),))
    db.execute("INSERT INTO fts(fts) VALUES('optimize')")
    db.commit()
    db.execute('VACUUM')
    db.close()
    log('db written', os.path.getsize(OUT_DB) // 1024, 'KB')


# ---------------------------------------------------------------- prepared PBF for the map writer
def write_pbf(D, feats, city, admin):
    from osmium.osm.mutable import Node, Way, Relation
    import build_sea
    cityp = shapely.prepared.prep(city['geom'])
    sid = [SYN_ID]

    def nid():
        sid[0] += 1
        return sid[0]

    node_tags = {}
    syn_nodes, syn_ways, syn_rels = [], [], []

    def label_tags(f):
        k = f['kind']
        name = '' if f.get('noname') else f['name']
        if k == KIND_ADMIN:
            if f['level'] > 8:
                return None
            return {'qd_admin': f['cls'], 'name': name}
        if k == KIND_PLACE:
            pl = f['tags'].get('place')
            if pl in ('city', 'town'):
                return None
            return {'place': pl, 'name': name}
        if k == KIND_ADDR:
            return {'poi': 'addr', 'addr:housenumber': f['tags'].get('addr:housenumber', '')}
        if k == KIND_POI:
            t = {'poi': f['cls']}
            if name:
                t['name'] = name
            for x in ('ele', 'addr:housenumber', 'ref'):
                if f['tags'].get(x):
                    t[x] = f['tags'][x]
            return t
        return None

    for f in feats:
        t = label_tags(f)
        if not t:
            continue
        osm = f.get('osm') or ''
        if f['kind'] == KIND_ADMIN and f['level'] == 5:
            c = next((p for p in D['places'] if p['tags'].get('place') == 'city' and p['name'] in ('青岛市', '青岛')), None)
            if c:
                f = dict(f, lon=c['lon'], lat=c['lat'])
        if osm.startswith('n') and f['kind'] != KIND_ADMIN:
            node_tags[int(osm[1:])] = t
        else:
            syn_nodes.append(Node(id=nid(), location=(f['lon'], f['lat']), tags=t))

    def add_ring(coords, tags):
        refs = []
        for x, y in coords[:-1]:  # closing point reuses the first node so the way is closed
            i = nid()
            syn_nodes.append(Node(id=i, location=(x, y), tags={}))
            refs.append(i)
        refs.append(refs[0])
        syn_ways.append(Way(id=nid(), nodes=refs, tags=tags))
        return syn_ways[-1].id

    # sea + land
    frame, land = build_sea.build()
    add_ring(list(frame.exterior.coords), {'natural': 'sea', 'layer': '-5'})
    for p in land:
        p = p.simplify(0.00001)
        if not p.interiors:
            add_ring(list(p.exterior.coords), {'natural': 'nosea', 'layer': '-5'})
        else:
            outer = add_ring(list(p.exterior.coords), {})
            inner = [add_ring(list(r.coords), {}) for r in p.interiors]
            syn_rels.append(Relation(id=nid(), members=[('w', outer, 'outer')] + [('w', w, 'inner') for w in inner],
                                     tags={'type': 'multipolygon', 'natural': 'nosea', 'layer': '-5'}))
    # administrative boundaries, clipped to land (+ small coastal margin)
    landbuf = unary_union(land).buffer(0.003)
    for a in [city] + admin:
        if a['level'] not in (5, 6, 8):
            continue
        kind = {5: 'city', 6: 'district', 8: 'town'}[a['level']]
        g = a['geom'].simplify(0.0002 if a['level'] <= 6 else 0.0003)
        rings = []
        for poly in (g.geoms if hasattr(g, 'geoms') else [g]):
            rings.append(LineString(poly.exterior.coords))
        lines = unary_union(rings).intersection(landbuf)
        for l in (lines.geoms if hasattr(lines, 'geoms') else [lines]):
            if l.geom_type == 'LineString' and len(l.coords) >= 2:
                refs = []
                for x, y in l.coords:
                    i = nid()
                    syn_nodes.append(Node(id=i, location=(x, y), tags={}))
                    refs.append(i)
                syn_ways.append(Way(id=nid(), nodes=refs, tags={'qd_boundary': kind}))
    log('synthetic', len(syn_nodes), 'nodes', len(syn_ways), 'ways', len(syn_rels), 'rels')

    if os.path.exists(OUT_PBF):
        os.remove(OUT_PBF)
    w = osmium.SimpleWriter(OUT_PBF)
    stage = 0  # 0 nodes, 1 ways, 2 relations

    def flush_to(s):
        nonlocal stage
        if stage < 1 <= s:
            for n in syn_nodes:
                w.add_node(n)
        if stage < 2 <= s:
            for x in syn_ways:
                w.add_way(x)
        if stage < 3 <= s:
            for r in syn_rels:
                w.add_relation(r)
        stage = max(stage, s)

    for o in osmium.FileProcessor(SRC):
        if o.is_node():
            t = None
            if o.id in node_tags:
                t = dict(tagdict(o), **node_tags[o.id])
            elif len(o.tags):
                ot = tagdict(o)
                if ot.get('highway') == 'bus_stop' and 'name' in ot and not ot.get('railway'):
                    t = dict(ot, poi='busstop')
                elif ot.get('place') in ('city', 'town') and not cityp.contains(Point(o.location.lon, o.location.lat)):
                    t = dict(ot, qd_admin='town' if ot['place'] == 'town' else 'district')
            w.add_node(o.replace(tags=t) if t is not None else o)
        elif o.is_way():
            flush_to(1)
            t = o.tags
            if 'building' in t and t.get('building') not in ('yes', 'no'):
                nt = tagdict(o)
                nt['building'] = 'yes'
                w.add_way(o.replace(tags=nt))
            else:
                w.add_way(o)
        else:
            flush_to(2)
            w.add_relation(o)
    flush_to(3)
    w.close()
    log('pbf written', os.path.getsize(OUT_PBF) // 1024, 'KB')


def main():
    os.makedirs('data/out', exist_ok=True)
    import pickle
    cache = 'data/extract.pickle'
    if os.path.exists(cache) and '--fresh' not in sys.argv:
        city, admin, routes, D = pickle.load(open(cache, 'rb'))
    else:
        city, admin = load_admin()
        routes = load_routes()
        D = extract(routes)
        pickle.dump((city, admin, routes, D), open(cache, 'wb'), protocol=4)
    locator = Locator(admin)
    import build_sea
    frame, land_polys = build_sea.build()
    land = unary_union(land_polys)
    feats = assemble(D, routes, city, admin, locator, land)
    write_db(feats)
    write_pbf(D, feats, city, admin)


if __name__ == '__main__':
    main()
