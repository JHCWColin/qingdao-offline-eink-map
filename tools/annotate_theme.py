"""Add independently switchable Mapsforge categories to the e-ink theme."""
from pathlib import Path
import xml.etree.ElementTree as ET

NS = 'http://mapsforge.org/renderTheme'
ET.register_namespace('', NS)
P = Path(__file__).resolve().parents[1] / 'app/src/main/assets/theme/qingdao_eink.xml'

POI_GROUP = {
    'airport': 'transport', 'train': 'transport', 'subway': 'transport',
    'ferry': 'transport', 'busstation': 'transport', 'fuel': 'transport',
    'parking': 'transport', 'subway_entrance': 'transport', 'busstop': 'transport',
    'mall': 'shop', 'market': 'shop', 'shop': 'shop', 'car': 'shop',
    'food': 'food', 'cafe': 'food', 'bar': 'food',
}
LAYER_CATEGORIES = (
    ('road', '道路线条'), ('roadname', '路名'), ('path', '步行小径'),
    ('pathname', '小径名称'), ('rail', '轨道线条'), ('railname', '轨道名称'),
    ('transport', '交通站点'), ('transportname', '交通站点名称'),
    ('placename', '地名'), ('poi', '公共设施图标'), ('poiname', '公共设施名称'),
    ('shop', '店铺图标'), ('shopname', '店名'),
    ('food', '餐饮图标'), ('foodname', '餐饮名称'),
    ('building', '建筑轮廓'), ('addr', '门牌号'),
    ('water', '水域'), ('watername', '水域名称'),
    ('landuse', '土地利用'), ('boundary', '行政边界'),
)


def local(tag):
    return tag.split('}')[-1]


def category_for(el, rules):
    tag = local(el.tag)
    context = {r.get('k'): r.get('v') for r in rules if r.get('k') not in (None, '*')}
    highway = context.get('highway', '')
    poi = context.get('poi', '')
    if tag == 'pathText':
        if highway:
            return 'pathname' if any(x in highway for x in ('footway', 'path', 'steps', 'cycleway', 'bridleway', 'track')) else 'roadname'
        if 'waterway' in context:
            return 'watername'
        if 'railway' in context:
            return 'railname'
        if 'route' in context:
            return 'transportname'
    if tag == 'caption':
        if poi:
            group = POI_GROUP.get(poi, 'poi')
            if group == 'shop':
                return 'shopname'
            if group == 'food':
                return 'foodname'
            if group == 'transport':
                return 'transportname'
            if poi == 'water':
                return 'watername'
            if poi == 'junction':
                return 'roadname'
            if poi == 'addr':
                return 'addr'
            if poi == 'estate':
                return 'placename'
            return 'poiname'
        if 'qd_admin' in context or 'place' in context:
            return 'placename'
        if 'building' in context:
            return 'addr'
    if tag == 'symbol':
        if poi:
            return POI_GROUP.get(poi, 'poi')
        if highway == 'traffic_signals':
            return 'road'
    if tag == 'lineSymbol':
        return 'road'
    if tag == 'area':
        if 'building' in context:
            return 'building'
        if context.get('natural') in ('sea|issea', 'water') or 'waterway' in context:
            return 'water'
        if context.get('landuse') == 'reservoir|basin|salt_pond|aquaculture':
            return 'water'
        if context.get('natural') == 'nosea':
            return None
        return 'landuse'
    if tag == 'line':
        if highway:
            return 'path' if any(x in highway for x in ('footway', 'path', 'steps', 'cycleway', 'bridleway', 'track')) else 'road'
        if 'qd_boundary' in context:
            return 'boundary'
        if 'railway' in context:
            return 'rail'
        if 'waterway' in context or context.get('natural') == 'coastline':
            return 'water'
        if 'route' in context or 'aerialway' in context or 'aeroway' in context:
            return 'transport'
        return 'landuse'
    return None


def annotate(path=P):
    tree = ET.parse(path)
    root = tree.getroot()
    for menu in list(root):
        if local(menu.tag) == 'stylemenu':
            root.remove(menu)
    menu = ET.Element(f'{{{NS}}}stylemenu', {'id': 'qingdao', 'defaultvalue': 'default', 'defaultlang': 'zh'})
    base = ET.SubElement(menu, f'{{{NS}}}layer', {'id': 'default', 'visible': 'true', 'enabled': 'true'})
    ET.SubElement(base, f'{{{NS}}}name', {'lang': 'zh', 'value': '标准'})
    for cat, title in LAYER_CATEGORIES:
        layer = ET.SubElement(menu, f'{{{NS}}}layer', {'id': cat, 'visible': 'true', 'enabled': 'true'})
        ET.SubElement(layer, f'{{{NS}}}name', {'lang': 'zh', 'value': title})
        ET.SubElement(layer, f'{{{NS}}}cat', {'id': cat})
    root.insert(0, menu)

    counts = {}
    def visit(node, rules):
        if local(node.tag) == 'rule':
            rules = rules + (node,)
        elif node is not root and node is not menu:
            cat = category_for(node, rules)
            if cat:
                node.set('cat', cat)
                counts[cat] = counts.get(cat, 0) + 1
        for child in node:
            visit(child, rules)
    for child in root:
        if child is not menu:
            visit(child, ())
    tree.write(path, encoding='UTF-8', xml_declaration=True)
    return counts


if __name__ == '__main__':
    print(annotate())
