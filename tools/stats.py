import osmium, collections
c = collections.Counter(); kv = collections.Counter()
KEYS = ('amenity','shop','tourism','leisure','office','healthcare','public_transport','railway','highway','building','landuse','natural','place','historic','man_made','sport','craft','aeroway','waterway','route')
for o in osmium.FileProcessor('data/qingdao.osm.pbf'):
    t = o.tags
    if len(t) == 0: continue
    named = 'name' in t
    c[o.type_str() + ('-named' if named else '')] += 1
    if 'addr:housenumber' in t: c['housenumber'] += 1
    if 'addr:street' in t: c['addr:street'] += 1
    if 'phone' in t or 'contact:phone' in t: c['phone'] += 1
    if 'opening_hours' in t: c['hours'] += 1
    for k in KEYS:
        if k in t and (named or k in ('highway','building','route')):
            kv[(k, t[k] if k not in ('building',) else '*')] += 1
print(c)
for (k,v),n in kv.most_common(150): print(k, v, n)
