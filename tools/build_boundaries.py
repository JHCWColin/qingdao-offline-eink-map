# Build Qingdao + district polygons from OSM admin relations.
import osmium, json
from shapely import wkb
from shapely.geometry import mapping

IDS = {3469133: '青岛市', 5655170: '平度市', 5655202: '莱西市', 5655231: '即墨区', 5655340: '胶州市',
       5655345: '黄岛区', 5655439: '市北区', 5655440: '市南区', 5655516: '崂山区', 5655557: '城阳区', 5655558: '李沧区'}

class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.f = osmium.geom.WKBFactory(); self.out = {}
    def area(self, a):
        if a.from_way(): return
        rid = a.orig_id()
        if rid in IDS:
            self.out[rid] = wkb.loads(self.f.create_multipolygon(a), hex=True)

h = H()
h.apply_file('data/shandong-latest.osm.pbf', locations=True, idx='flex_mem',
             filters=[osmium.filter.KeyFilter('boundary')])
feats = []
for rid, g in h.out.items():
    feats.append({'type': 'Feature', 'properties': {'id': rid, 'name': IDS[rid]}, 'geometry': mapping(g)})
    print(rid, IDS[rid], g.geom_type, [round(x, 3) for x in g.bounds], round(g.area, 4))
json.dump({'type': 'FeatureCollection', 'features': feats}, open('data/boundaries.geojson', 'w', encoding='utf-8'), ensure_ascii=False)
