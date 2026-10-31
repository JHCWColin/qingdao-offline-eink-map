import osmium, sys
fp = osmium.FileProcessor('data/shandong-latest.osm.pbf', osmium.osm.RELATION)
for r in fp:
    t = r.tags
    if t.get('boundary') == 'administrative' and t.get('admin_level') in ('5','6'):
        n = t.get('name','')
        print(r.id, t.get('admin_level'), n, t.get('ref:gb',''))
