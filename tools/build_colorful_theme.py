"""Build the committed Colorful theme from the existing detailed map rules.

Run from any directory: python tools/build_colorful_theme.py
Preserves category controls, labels and zoom rules; replaces grayscale styling.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'app/src/main/assets/theme'
OUTPUT = ROOT / 'colorful/src/main/assets/theme'
NS = 'http://mapsforge.org/renderTheme'
ET.register_namespace('', NS)
tree = ET.parse(SOURCE / 'qingdao_eink.xml')
theme = tree.getroot()
theme.set('map-background', '#AAD7EC')
theme.set('map-background-outside', '#AAD7EC')
# OSM nature reserves can be marine polygons that cover open water. Their
# boundaries do not imply land cover, so let the underlying sea/land show.
for rule in theme.iter():
    if (rule.tag.rsplit('}', 1)[-1] == 'rule'
            and rule.get('k') == 'leisure'
            and rule.get('v') == 'park|garden|nature_reserve|golf_course'):
        rule.set('v', 'park|garden|golf_course')
icon_colors = {}
PALETTE = {'shop': '#8B5CF6', 'shopname': '#7C3AED',
           'food': '#EA580C', 'foodname': '#C2410C',
           'transport': '#2563EB', 'transportname': '#1D4ED8',
           'poi': '#0F766E', 'poiname': '#0F766E',
           'water': '#76BCE0', 'watername': '#287EB0',
           'rail': '#64748B', 'railname': '#475569',
           'boundary': '#A78BBA', 'placename': '#334155',
           'roadname': '#394454', 'pathname': '#766A54', 'addr': '#78716C'}


def visit(node, rules=()):
    tag = node.tag.rsplit('}', 1)[-1]
    if tag == 'rule':
        rules = rules + ((node.get('k', ''), node.get('v', '')),)
    cat = node.get('cat', '')
    color = PALETTE.get(cat, '#475569')
    if tag == 'area':
        pattern = node.attrib.pop('src', '')
        fill = {'hatch.png': '#E5DDEB', 'construction.png': '#ECDCC7',
                'military.png': '#DDDDBF', 'cemetery.png': '#C8DBBF',
                'park.png': '#C8E6BF', 'wood.png': '#ADD4A1',
                'sand.png': '#F3E5B0', 'marsh.png': '#BFDED1'}.get(Path(pattern).name)
        if cat == 'water':
            fill = '#AAD7EC'
        elif cat == 'building':
            fill = '#DDD6CF'
        elif not fill:
            for key, value in reversed(rules):
                if key == 'landuse':
                    fill = '#EBE9E3' if 'residential' in value else '#E4DEEA'
                    break
                if key == 'leisure':
                    fill = '#C7E4C4'
                    break
                if key == 'amenity':
                    fill = '#F3DFDF' if 'hospital' in value else '#F0E8CD'
                    break
                if key == 'aeroway':
                    fill = '#DDE3EC'
                    break
        if fill:
            node.set('fill', fill)
        if 'stroke' in node.attrib:
            node.set('stroke', '#C1B9B0' if cat == 'building' else '#A7B9AC')
    elif tag == 'line':
        if cat == 'road':
            highway = next((v for k, v in reversed(rules)
                            if k == 'highway' and v != '*'), '')
            interior = node.get('stroke', '').upper() in ('#FFFFFF', '#F2F2F2', '#FAFAFA')
            road = '#FFFFFF' if interior else '#D1CCC3'
            if 'motorway' in highway:
                road = '#F3A6A6' if interior else '#DC7778'
            elif 'trunk' in highway or 'primary' in highway:
                road = '#F5BF83' if interior else '#D49A5C'
            elif 'secondary' in highway:
                road = '#F9DA8C' if interior else '#C9A857'
            elif 'tertiary' in highway:
                road = '#FFF0B3' if interior else '#B8A56E'
            node.set('stroke', road)
        else:
            node.set('stroke', '#B39570' if cat == 'path' else color)
    elif tag in ('caption', 'pathText'):
        node.set('fill', color)
        if 'stroke' in node.attrib:
            node.set('stroke', '#FFFFFF')
    elif tag in ('symbol', 'lineSymbol'):
        src = node.get('src', '')
        if src:
            icon_colors[src] = color
    for child in node:
        visit(child, rules)


visit(theme)
OUTPUT.mkdir(parents=True, exist_ok=True)
ET.indent(tree, space='  ')
tree.write(OUTPUT / 'qingdao_colorful.xml', encoding='utf-8', xml_declaration=True)
for source in (SOURCE / 'symbols').glob('*.svg'):
    target = OUTPUT / 'symbols' / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    name = source.stem
    color = icon_colors.get('symbols/' + source.name, '#0F766E')
    if name in {'airport', 'busstation', 'busstop', 'car', 'ferry', 'fuel', 'oneway', 'subway',
                'subway_entrance', 'train', 'traffic_signals'}:
        color = '#2563EB'
    elif name in {'cafe', 'food', 'bar'}:
        color = '#EA580C'
    elif name in {'mall', 'market', 'shop'}:
        color = '#8B5CF6'
    elif name in {'park', 'peak', 'sight', 'estate'}:
        color = '#16A34A'
    elif name in {'hospital', 'clinic', 'pharmacy'}:
        color = '#DC2626'
    elif name in {'building', 'office', 'hotel', 'bank', 'gov'}:
        color = '#475569'
    svg = source.read_text('utf-8')
    svg = re.sub(r'#(?:000000|000)\b', color, svg, flags=re.I)
    target.write_text(svg, encoding='utf-8')
print('Colorful theme and symbols written to', OUTPUT)
