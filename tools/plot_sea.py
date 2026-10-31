import xml.etree.ElementTree as ET, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
r = ET.parse('data/sea.osm').getroot(); n = {e.get('id'): (float(e.get('lon')), float(e.get('lat'))) for e in r.iter('node')}
fig, ax = plt.subplots(figsize=(8, 7))
for w in r.iter('way'):
    t = {x.get('k'): x.get('v') for x in w.iter('tag')}; pts = [n[x.get('ref')] for x in w.iter('nd')]
    ax.fill([p[0] for p in pts], [p[1] for p in pts], color='#9cf' if t.get('natural') == 'sea' else '#eee', lw=0.3, ec='k')
fig.savefig('data/sea.png', dpi=80)
